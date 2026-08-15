from src.helper import _get_windows_default_communications_device_name


def test_get_windows_default_communications_device_name_handles_exceptions():
    result = _get_windows_default_communications_device_name()
    assert result is None or isinstance(result, str)
