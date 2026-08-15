import os
import sys

from src.utils.paths import get_asset_path


def test_get_asset_path_dev_environment(monkeypatch):
    # Ensure sys._MEIPASS is absent
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    path = os.path.normpath(get_asset_path("src/assets/logo.png"))
    expected_suffix = os.path.join("src", "assets", "logo.png")
    assert path.endswith(expected_suffix)
    assert os.path.isabs(path)


def test_get_asset_path_frozen_meipass(monkeypatch):
    fake_meipass = os.path.abspath("C:\\Temp\\_MEIPASS12345")
    monkeypatch.setattr(sys, "_MEIPASS", fake_meipass, raising=False)

    path = get_asset_path("src/assets/branding/logo.ico")
    expected = os.path.join(fake_meipass, "src/assets/branding/logo.ico")
    assert os.path.normpath(path) == os.path.normpath(expected)
