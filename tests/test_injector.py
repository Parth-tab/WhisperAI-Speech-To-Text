from unittest.mock import patch

from src.injection.injector import ClipboardInjector, send_unicode_text


@patch("src.injection.injector.send_unicode_text", return_value=True)
def test_sendinput_preferred_injection(mock_send_unicode):
    injector = ClipboardInjector(prefer_sendinput=True)
    injector.inject_text("Hello World 🎙️")
    mock_send_unicode.assert_called_once_with("Hello World 🎙️")


@patch("src.injection.injector.pyperclip")
@patch("src.injection.injector.pyautogui")
@patch("src.injection.injector.time.sleep")
def test_fallback_clipboard_injection(mock_sleep, mock_pyautogui, mock_pyperclip):
    mock_pyperclip.paste.return_value = "old_clipboard"
    injector = ClipboardInjector(prefer_sendinput=False)

    injector.inject_text("new_text")

    mock_pyperclip.copy.assert_any_call("new_text")
    mock_pyautogui.hotkey.assert_called_once_with("ctrl", "v")
    mock_sleep.assert_any_call(0.05)
    mock_pyperclip.copy.assert_any_call("old_clipboard")


def test_send_unicode_text_handles_emojis_and_surrogates():
    # Test UTF-16 surrogate string conversion logic without throwing errors
    with patch("ctypes.windll.user32.SendInput") as mock_send_input:
        mock_send_input.return_value = 2
        res = send_unicode_text("Test 🎙️ 😊")
        assert res is True
        assert mock_send_input.called


def test_send_unicode_text_rejects_partial_injection():
    with patch("ctypes.windll.user32.SendInput") as mock_send_input:
        mock_send_input.return_value = 1
        res = send_unicode_text("A", delay_ms=0)
        assert res is False



@patch("src.injection.injector.send_unicode_text")
@patch("src.injection.injector.pyperclip")
@patch("src.injection.injector.pyautogui")
@patch("src.injection.injector.time.sleep")
def test_notepad_clipboard_fallback(mock_sleep, mock_pyautogui, mock_pyperclip, mock_send_unicode):
    mock_pyperclip.paste.return_value = "old_clip"
    injector = ClipboardInjector(prefer_sendinput=True)

    injector.inject_text("Notepad test string", process_name="notepad.exe")

    # send_unicode_text should NOT be called for notepad.exe
    mock_send_unicode.assert_not_called()
    mock_pyperclip.copy.assert_any_call("Notepad test string")
    mock_pyautogui.hotkey.assert_called_once_with("ctrl", "v")

