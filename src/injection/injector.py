import pyperclip
import pyautogui
import time

class ClipboardInjector:
    def __init__(self):
        pass

    def inject_text(self, text: str):
        original_clipboard = ""
        for _ in range(5):
            try:
                original_clipboard = pyperclip.paste()
                break
            except Exception as e:
                print(f"[Injector] Failed to get clipboard: {e}")
                time.sleep(0.1)

        for _ in range(5):
            try:
                pyperclip.copy(text)
                if pyperclip.paste() == text:
                    break
            except Exception as e:
                print(f"[Injector] Failed to copy text: {e}")
                time.sleep(0.1)

        # Simulate Ctrl+V
        pyautogui.hotkey('ctrl', 'v')

        # Give slight delay to allow OS to process paste
        time.sleep(0.1)

        if original_clipboard:
            for _ in range(5):
                try:
                    pyperclip.copy(original_clipboard)
                    break
                except Exception:
                    time.sleep(0.1)
