import pytest
from unittest.mock import patch
from src.injection.injector import ClipboardInjector

@patch('src.injection.injector.pyperclip')
@patch('src.injection.injector.pyautogui')
@patch('src.injection.injector.time.sleep')
def test_injector(mock_sleep, mock_pyautogui, mock_pyperclip):
    mock_pyperclip.paste.return_value = "old_clipboard"
    injector = ClipboardInjector()
    
    injector.inject_text("new_text")
    
    mock_pyperclip.copy.assert_any_call("new_text")
    mock_pyautogui.hotkey.assert_called_once_with('ctrl', 'v')
    mock_sleep.assert_any_call(0.1)
    mock_pyperclip.copy.assert_any_call("old_clipboard")
