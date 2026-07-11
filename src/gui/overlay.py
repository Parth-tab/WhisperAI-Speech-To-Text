from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

class RecordingOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout()
        self.label = QLabel("🔴 Recording...")
        self.label.setStyleSheet("""
            QLabel {
                color: red;
                background-color: rgba(0, 0, 0, 150);
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.position_overlay()

    def position_overlay(self):
        # Position near bottom right as fallback
        screen = QGuiApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 50
        y = screen.height() - self.height() - 50
        self.move(x, y)

    def show_overlay(self):
        self.position_overlay()
        self.show()

    def hide_overlay(self):
        self.hide()
