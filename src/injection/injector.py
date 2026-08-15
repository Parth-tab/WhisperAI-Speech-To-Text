import ctypes
import logging
import struct
import time
from ctypes import wintypes

import pyautogui
import pyperclip

logger = logging.getLogger("whisperai")

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT_UNION),
    ]


def send_unicode_text(text: str, delay_ms: float = 0.5) -> bool:
    """Inject text directly into active caret focus using Win32 SendInput.
    Encodes via UTF-16-LE to safely safely send surrogate pairs for non-BMP characters/emojis.
    Bypasses the system clipboard entirely.
    """
    try:
        user32 = ctypes.windll.user32
        delay_sec = delay_ms / 1000.0 if delay_ms > 0 else 0.0

        for char in text:
            if char == "\n":
                inputs = (INPUT * 2)()
                inputs[0].type = INPUT_KEYBOARD
                inputs[0].u.ki.wVk = 0x0D  # VK_RETURN
                inputs[1].type = INPUT_KEYBOARD
                inputs[1].u.ki.wVk = 0x0D
                inputs[1].u.ki.dwFlags = KEYEVENTF_KEYUP
                res = user32.SendInput(2, inputs, ctypes.sizeof(INPUT))
                if res != len(inputs):
                    if res > 0:
                        logger.error("[Injector] Partial SendInput failure: KeyDown succeeded but KeyUp was blocked by OS.")
                    return False
                if delay_sec > 0:
                    time.sleep(delay_sec)
                continue

            # Encode to UTF-16-LE byte sequence to extract 16-bit code units (handles emojis/surrogates)
            utf16_bytes = char.encode("utf-16-le")
            for i in range(0, len(utf16_bytes), 2):
                code_unit = struct.unpack("<H", utf16_bytes[i : i + 2])[0]
                input_down = INPUT(
                    type=INPUT_KEYBOARD,
                    u=_INPUT_UNION(
                        ki=KEYBDINPUT(0, code_unit, KEYEVENTF_UNICODE, 0, 0)
                    ),
                )
                input_up = INPUT(
                    type=INPUT_KEYBOARD,
                    u=_INPUT_UNION(
                        ki=KEYBDINPUT(
                            0, code_unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0
                        )
                    ),
                )
                inputs = (INPUT * 2)(input_down, input_up)
                res = user32.SendInput(2, inputs, ctypes.sizeof(INPUT))
                if res != len(inputs):
                    if res > 0:
                        logger.error("[Injector] Partial SendInput failure: KeyDown succeeded but KeyUp was blocked by OS.")
                    return False
                if delay_sec > 0:
                    time.sleep(delay_sec)
        return True
    except Exception as e:
        logger.error(f"[Injector] SendInput failed: {e}")
        return False


class ClipboardInjector:
    def __init__(self, prefer_sendinput: bool = True):
        self.prefer_sendinput = prefer_sendinput

    @staticmethod
    def is_bidi_script(text: str) -> bool:
        """Detect bidirectional, Arabic, Hebrew, Devanagari, or complex scripts requiring atomic paste."""
        import re
        return bool(re.search(r"[\u0600-\u06FF\u0590-\u05FF\u0900-\u097F\u0700-\u074F\u0780-\u07BF\uFB50-\uFDFF\uFE70-\uFEFF]", text))

    def inject_text(self, text: str, process_name: str = ""):
        from src.llm.formatter import Formatter
        from src.utils.text_cleaner import sanitize_symbol_loops

        try:
            Formatter().check_repetition(text)
        except ValueError as e:
            logger.warning(f"[Injector] Aborted injection: {e}")
            return

        text = sanitize_symbol_loops(text)
        if not text:
            return

        import re
        if re.search(r"([a-zA-Z])\1{4,}|([.,;:!?])\1{4,}|0{12,}", text):
            logger.warning("[Injector] Aborted injection of repeating text loop.")
            return

        known_clipboard_apps = {"notepad.exe", "notepad++.exe"}
        proc_lower = process_name.lower().strip() if process_name else ""
        if not proc_lower:
            try:
                from src.injection.window_detect import WindowDetector
                _, proc_lower, _ = WindowDetector().get_active_window_info()
                proc_lower = proc_lower.lower().strip()
            except Exception:
                pass

        # Multi-Modal Threshold:
        # If text is short (<100 chars), single-line, AND not a BiDi/RTL script -> use zero-clipboard SendInput directly at caret.
        # If text is long (>=100 chars), contains newlines, or is a BiDi script -> use atomic clipboard paste to prevent Win32 caret/buffer issues.
        is_short_single_line = len(text) < 100 and "\n" not in text and not self.is_bidi_script(text)

        if self.prefer_sendinput and proc_lower not in known_clipboard_apps and is_short_single_line:
            success = send_unicode_text(text)
            if success:
                return

        # Clipboard Ctrl+V injection for long text, multi-line blocks, or SendInput fallbacks
        windows_safe_text = text.replace("\r\n", "\n").replace("\n", "\r\n")
        original_clipboard = ""
        for _ in range(5):
            try:
                original_clipboard = pyperclip.paste()
                break
            except Exception as e:
                logger.warning(f"[Injector] Failed to get clipboard: {e}")
                time.sleep(0.05)

        for _ in range(5):
            try:
                pyperclip.copy(windows_safe_text)
                if pyperclip.paste() == windows_safe_text:
                    break
            except Exception as e:
                logger.warning(f"[Injector] Failed to copy text: {e}")
                time.sleep(0.05)

        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.05)

        if original_clipboard:
            for _ in range(5):
                try:
                    pyperclip.copy(original_clipboard)
                    break
                except Exception:
                    time.sleep(0.05)
