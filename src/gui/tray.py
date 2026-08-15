from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from src.gui.settings import SettingsWindow
from src.utils.paths import get_asset_path


class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, app, config_manager, quit_callback, settings_callback=None):
        super().__init__()
        self.app = app
        self.config_manager = config_manager
        self.quit_callback = quit_callback
        self.settings_callback = settings_callback

        self.set_icon()

        self.menu = QMenu()

        self.settings_action = self.menu.addAction("Settings")
        self.settings_action.triggered.connect(self.show_settings)

        self.stats_action = self.menu.addAction("Usage Stats")
        self.stats_action.triggered.connect(self.show_stats)

        self.quit_action = self.menu.addAction("Quit")
        self.quit_action.triggered.connect(self.quit_app)

        self.setContextMenu(self.menu)

        self.settings_window = None
        self.stats_dialog = None

    def set_icon(self):
        icon_path = get_asset_path("src/assets/branding/logo.ico")
        self.setIcon(QIcon(icon_path))

    def show_settings(self):
        try:
            if self.settings_window is not None:
                self.settings_window.show()
                self.settings_window.activateWindow()
                return
        except RuntimeError:
            self.settings_window = None

        self.settings_window = SettingsWindow(self.config_manager)
        if self.settings_callback:
            self.settings_window.settings_saved.connect(self.settings_callback)
        self.settings_window.show()
        self.settings_window.activateWindow()

    def show_stats(self):
        from src.gui.widgets.stats_dialog import StatsDialog

        try:
            if self.stats_dialog is not None:
                self.stats_dialog.show()
                self.stats_dialog.raise_()
                self.stats_dialog.activateWindow()
                return
        except RuntimeError:
            self.stats_dialog = None

        self.stats_dialog = StatsDialog()
        self.stats_dialog.show()
        self.stats_dialog.raise_()
        self.stats_dialog.activateWindow()

    def quit_app(self):
        self.quit_callback()
        self.app.quit()
