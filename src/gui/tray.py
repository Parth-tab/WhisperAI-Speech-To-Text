from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
from src.gui.settings import SettingsWindow

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
        
        self.quit_action = self.menu.addAction("Quit")
        self.quit_action.triggered.connect(self.quit_app)
        
        self.setContextMenu(self.menu)
        
        self.settings_window = None

    def set_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor("red"))
        painter.drawEllipse(2, 2, 28, 28)
        painter.end()
        self.setIcon(QIcon(pixmap))

    def show_settings(self):
        if not self.settings_window:
            self.settings_window = SettingsWindow(self.config_manager)
            if self.settings_callback:
                self.settings_window.settings_saved.connect(self.settings_callback)
        self.settings_window.show()
        self.settings_window.activateWindow()

    def quit_app(self):
        self.quit_callback()
        self.app.quit()
