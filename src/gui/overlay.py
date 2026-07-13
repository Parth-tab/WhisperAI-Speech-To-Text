import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QPainter, QColor, QPen, QBrush

class RecordingOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.level = 0.0
        self.target_level = 0.0
        self.resize(200, 200)

        # Timer for smooth animation
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(16) # ~60fps

    def position_overlay(self):
        screen = QGuiApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 50
        y = screen.height() - self.height() - 50
        self.move(x, y)

    def show_overlay(self):
        self.position_overlay()
        self.level = 0.0
        self.target_level = 0.0
        self.show()

    def hide_overlay(self):
        self.hide()

    def update_level(self, level: float):
        self.target_level = min(1.0, level * 15.0)

    def animate(self):
        if not self.isVisible():
            return
        self.level += (self.target_level - self.level) * 0.2
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        base_radius = 20
        dynamic_radius = base_radius + (self.level * 40)

        # Draw glow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 150, 255, 80))
        painter.drawEllipse(int(center_x - dynamic_radius - 10), int(center_y - dynamic_radius - 10), 
                            int((dynamic_radius + 10) * 2), int((dynamic_radius + 10) * 2))

        # Draw inner bubble
        painter.setBrush(QColor(0, 150, 255, 200))
        painter.drawEllipse(int(center_x - dynamic_radius), int(center_y - dynamic_radius), 
                            int(dynamic_radius * 2), int(dynamic_radius * 2))
