from src.injection.window_detect import is_terminal_process
from src.utils.caret_tracker import (
    get_active_caret_coordinates,
    get_workarea_fallback_coords,
)
from src.utils.theme_compiler import THEME_TOKENS, compile_qss


def test_theme_compiler():
    template = "QDialog { background-color: {{bg_primary}}; color: {{text_primary}}; }"
    compiled = compile_qss(template, "dark")
    assert THEME_TOKENS["dark"]["bg_primary"] in compiled
    assert THEME_TOKENS["dark"]["text_primary"] in compiled
    assert "{{" not in compiled and "}}" not in compiled


def test_is_terminal_process():
    assert is_terminal_process("cmd.exe") is True
    assert is_terminal_process("PowerShell.exe") is True
    assert is_terminal_process("WindowsTerminal.exe") is True
    assert is_terminal_process("code.exe") is False
    assert is_terminal_process("chrome.exe") is False
    assert is_terminal_process("") is False


def test_caret_tracker_fallback():
    coords = get_workarea_fallback_coords()
    assert isinstance(coords, tuple)
    assert len(coords) == 2
    assert coords[0] > 0 and coords[1] > 0

    active_coords = get_active_caret_coordinates()
    assert isinstance(active_coords, tuple)
    assert len(active_coords) == 2
