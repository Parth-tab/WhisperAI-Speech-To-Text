import sys
import ctypes
from ctypes import wintypes
from enum import Enum

from PySide6.QtWidgets import QApplication, QWidget, QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QRect,
    QEasingCurve,
    QTimer,
    Signal,
    QSize,
)
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap
from src.utils.paths import get_asset_path


def set_no_activate(hwnd):
    GWL_EXSTYLE = -20
    WS_EX_NOACTIVATE = 0x08000000

    if sys.maxsize > 2**32:
        GetWindowLong = ctypes.windll.user32.GetWindowLongPtrW
        SetWindowLong = ctypes.windll.user32.SetWindowLongPtrW
    else:
        GetWindowLong = ctypes.windll.user32.GetWindowLongW
        SetWindowLong = ctypes.windll.user32.SetWindowLongW

    GetWindowLong.restype = ctypes.c_ssize_t
    GetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int]

    SetWindowLong.restype = ctypes.c_ssize_t
    SetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]

    ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
    if ex_style != 0 or ctypes.GetLastError() == 0:
        SetWindowLong(hwnd, GWL_EXSTYLE, ex_style | WS_EX_NOACTIVATE)


class WaveformWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.bars = 7
        self.levels = [0.0] * self.bars
        self.setMinimumWidth(80)
        self.setFixedHeight(30)

    def update_level(self, rms):
        self.levels.pop(0)
        self.levels.append(min(1.0, rms * 15.0))  # Scale appropriately
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bar_width = 4
        spacing = 4

        total_width = self.bars * bar_width + (self.bars - 1) * spacing
        start_x = (self.width() - total_width) // 2

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#A3E635"))

        for i, level in enumerate(self.levels):
            h = max(4, int(level * self.height()))
            x = start_x + i * (bar_width + spacing)
            y = (self.height() - h) // 2
            painter.drawRoundedRect(x, y, bar_width, h, 2, 2)


class SpinnerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(30)
        self.setFixedSize(30, 30)

    def rotate(self):
        self.angle = (self.angle + 15) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)

        pen = QPen(QColor("#FFFFFF"), 3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        rect = QRect(-10, -10, 20, 20)
        painter.drawArc(rect, 0, 270 * 16)


class BubbleState(Enum):
    IDLE = 0
    RECORDING = 1
    PROCESSING = 2


class FlowBubble(QWidget):
    clicked = Signal()

    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.state = BubbleState.IDLE
        self.drag_pos = None
        self.click_pos = None

        self.setFixedSize(50, 50)
        self.setWindowOpacity(0.6)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.bg_frame = QFrame(self)
        self.bg_frame.setStyleSheet("""
            QFrame {
                background-color: #111111;
                border-radius: 25px;
            }
        """)
        self.bg_layout = QHBoxLayout(self.bg_frame)
        self.bg_layout.setContentsMargins(10, 10, 10, 10)
        self.bg_layout.setSpacing(10)
        self.bg_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.layout.addWidget(self.bg_frame)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(30, 30)
        self.icon_label.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(get_asset_path("src/assets/branding/logo.png"))
        self.icon_label.setPixmap(
            pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

        self.icon_label.setStyleSheet("background-color: white; border-radius: 15px;")

        self.bg_layout.addWidget(self.icon_label)

        self.waveform = WaveformWidget()
        self.waveform.hide()
        self.bg_layout.addWidget(self.waveform)

        self.spinner = SpinnerWidget()
        self.spinner.hide()
        self.bg_layout.addWidget(self.spinner)

        self.anim = QPropertyAnimation(self, b"size")
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.setDuration(250)

        self._load_position()

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        set_no_activate(hwnd)

    def _load_position(self):
        if self.config_manager:
            pos = self.config_manager.get("bubble_pos", None)
            if pos and len(pos) == 2:
                self.move(pos[0], pos[1])
            else:
                screen = QApplication.primaryScreen().geometry()
                self.move(screen.width() - 300, screen.height() - 200)

    def _save_position(self):
        if self.config_manager:
            self.config_manager.set("bubble_pos", [self.x(), self.y()])

    def enterEvent(self, event):
        if self.state == BubbleState.IDLE:
            self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.state == BubbleState.IDLE:
            self.setWindowOpacity(0.6)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            self.click_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.drag_pos is not None:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.pos() + delta)
            self.drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.click_pos is not None:
                dist = (
                    event.globalPosition().toPoint() - self.click_pos
                ).manhattanLength()
                if dist < 5:
                    self.clicked.emit()
            self.drag_pos = None
            self.click_pos = None
            self._save_position()

    def set_state(self, state: BubbleState):
        self.state = state
        if state == BubbleState.IDLE:
            self.setWindowOpacity(0.6)
            self.waveform.hide()
            self.spinner.hide()
            self.icon_label.setStyleSheet(
                "background-color: white; border-radius: 15px;"
            )
            self.animate_size(50, 50)
        elif state == BubbleState.RECORDING:
            self.setWindowOpacity(1.0)
            self.waveform.show()
            self.spinner.hide()
            is_whisper = (
                self.config_manager.get("whisper_mode", False)
                if self.config_manager
                else False
            )
            color = "#A855F7" if is_whisper else "#EF4444"
            self.icon_label.setStyleSheet(
                f"background-color: {color}; border-radius: 15px;"
            )
            self.animate_size(150, 50)
        elif state == BubbleState.PROCESSING:
            self.setWindowOpacity(1.0)
            self.waveform.hide()
            self.spinner.show()
            self.icon_label.setStyleSheet(
                "background-color: #F59E0B; border-radius: 15px;"
            )
            self.animate_size(110, 50)

    def animate_size(self, w, h):
        self.anim.setStartValue(self.size())
        self.anim.setEndValue(QSize(w, h))
        self.anim.start()

    def update_audio_level(self, rms: float):
        if self.state == BubbleState.RECORDING:
            self.waveform.update_level(rms)
