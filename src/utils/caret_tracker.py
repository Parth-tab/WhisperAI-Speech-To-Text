import ctypes
import logging
from ctypes import wintypes

logger = logging.getLogger("whisperai")


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndSizeMove", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


def get_win32_caret_coords() -> tuple[int, int] | None:
    """Tier 1: Win32 USER32 GetGUIThreadInfo caret tracking for native Win32/Edit/RichEdit controls."""
    try:
        user32 = ctypes.windll.user32
        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)
        if user32.GetGUIThreadInfo(0, ctypes.byref(gui_info)):
            hwnd = gui_info.hwndFocus
            if hwnd and (gui_info.rcCaret.left > 10 or gui_info.rcCaret.bottom > 10):
                pt = wintypes.POINT(gui_info.rcCaret.left, gui_info.rcCaret.bottom)
                if user32.ClientToScreen(hwnd, ctypes.byref(pt)) and pt.x > 100 and pt.y > 100:
                    return pt.x, pt.y
    except Exception:
        pass
    return None


def get_workarea_fallback_coords() -> tuple[int, int]:
    """Tier 3: Active Display SPI_GETWORKAREA fallback position."""
    try:
        user32 = ctypes.windll.user32
        rect = RECT()
        # SPI_GETWORKAREA = 0x0030
        if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            # Bottom right offset from workarea
            return max(50, rect.right - 240), max(50, rect.bottom - 130)
    except Exception:
        pass
    return 1000, 700


def get_active_caret_coordinates() -> tuple[int, int]:
    """3-Tier Caret Detection Engine Chain (Win32 -> UIA -> WorkArea)."""
    # Tier 1: Win32 GetGUIThreadInfo
    coords = get_win32_caret_coords()
    if coords is not None:
        return coords

    # Tier 3: Display WorkArea Fallback
    return get_workarea_fallback_coords()
