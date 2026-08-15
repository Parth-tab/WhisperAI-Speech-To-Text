import logging
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from src.config.manager import ConfigManager
from src.gui.tray import SystemTrayApp
from src.utils.logger import setup_logger


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_setup_logger():
    log = setup_logger("TestLogger", logging.INFO)
    assert log.name == "TestLogger"
    assert log.level == logging.INFO
    assert len(log.handlers) >= 1


def test_system_tray_app(qapp):
    mock_app = MagicMock()
    mock_quit = MagicMock()
    mock_settings_cb = MagicMock()
    cfg = ConfigManager()

    tray = SystemTrayApp(mock_app, cfg, mock_quit, mock_settings_cb)
    assert tray.menu is not None
    assert len(tray.menu.actions()) == 3

    # Test show settings
    tray.show_settings()
    assert tray.settings_window is not None
    tray.settings_window.close()

    # Test show stats
    tray.show_stats()
    assert tray.stats_dialog is not None
    tray.stats_dialog.close()

    # Test quit
    tray.quit_app()
    mock_quit.assert_called_once()
    mock_app.quit.assert_called_once()
