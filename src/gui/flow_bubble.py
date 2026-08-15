import ctypes
import sys
from ctypes import wintypes
from enum import Enum

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from src.utils.paths import get_asset_path
from src.utils.theme_compiler import compile_qss


def set_no_activate(hwnd):
    GWL_EXSTYLE = -20
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TOOLWINDOW = 0x00000080

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
        target_style = ex_style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
        if ex_style != target_style:
            SetWindowLong(hwnd, GWL_EXSTYLE, target_style)
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_FRAMECHANGED = 0x0020
            ctypes.windll.user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
            )


class WaveformWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.bars = 7
        self.levels = [0.0] * self.bars
        self.setMinimumWidth(80)
        self.setFixedHeight(30)

    def update_level(self, rms):
        self.levels.pop(0)
        self.levels.append(min(1.0, rms * 15.0))
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

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.state = BubbleState.IDLE
        self.drag_pos = None
        self.click_pos = None

        # Parent margin container layout to host QGraphicsDropShadowEffect cleanly
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)

        self.bg_frame = QFrame(self)
        qss_template = """
            QFrame {
                background-color: {{bg_bubble}};
                border-radius: 25px;
            }
        """
        self.bg_frame.setStyleSheet(compile_qss(qss_template, "dark"))

        # Attach clean drop shadow to inner QFrame
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.bg_frame.setGraphicsEffect(shadow)

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

        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("color: #E2E8F0; font-size: 11px; font-weight: 500;")
        self.preview_label.hide()
        self.bg_layout.addWidget(self.preview_label)

        self.spinner = SpinnerWidget()
        self.spinner.hide()
        self.bg_layout.addWidget(self.spinner)

        self.setMinimumSize(74, 74)
        self.setMaximumSize(16777215, 16777215)
        self.resize(74, 74)
        self.setWindowOpacity(0.6)

        # Animations
        self.anim_size = QPropertyAnimation(self, b"size")
        self.anim_size.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_size.setDuration(250)

        self.anim_move = QPropertyAnimation(self, b"pos")
        self.anim_move.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_move.setDuration(200)

        self._load_position()

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        set_no_activate(hwnd)

    def _load_position(self):
        if self.config_manager:
            pos = self.config_manager.get("bubble_pos", None)
            if pos and len(pos) == 2 and pos[0] > 0 and pos[1] > 0:
                self.move(pos[0], pos[1])
                return

        self.update_position_near_caret(force=True)

    def update_position_near_caret(self, force: bool = False):
        """Update bubble location near active text cursor ONLY if a valid text caret is detected."""
        from src.utils.caret_tracker import get_win32_caret_coords
        coords = get_win32_caret_coords()
        if coords is None:
            return  # Stay anchored in current position; do NOT jump to workarea fallbacks!

        x, y = coords
        target_x = max(10, x + 10)
        target_y = max(10, y + 20)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            target_x = max(geo.left() + 10, min(target_x, geo.right() - self.width() - 10))
            target_y = max(geo.top() + 10, min(target_y, geo.bottom() - self.height() - 10))

        curr_pos = self.pos()
        dx = abs(curr_pos.x() - target_x)
        dy = abs(curr_pos.y() - target_y)

        if force or dx >= 25 or dy >= 25:
            self.smooth_move(target_x, target_y)

    def smooth_move(self, x: int, y: int):
        self.anim_move.setStartValue(self.pos())
        self.anim_move.setEndValue(QPoint(x, y))
        self.anim_move.start()

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
        self.show()
        self.raise_()

        if state == BubbleState.RECORDING:
            self.update_position_near_caret(force=False)

        if state == BubbleState.IDLE:
            self.setWindowOpacity(0.6)
            self.waveform.hide()
            self.spinner.hide()
            self.preview_label.hide()
            self.preview_label.setText("")
            self.icon_label.setStyleSheet(
                "background-color: white; border-radius: 15px;"
            )
            self.animate_size(74, 74)
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
            self.animate_size(174, 74)
        elif state == BubbleState.PROCESSING:
            self.setWindowOpacity(1.0)
            self.waveform.hide()
            self.preview_label.hide()
            self.spinner.show()
            self.icon_label.setStyleSheet(
                "background-color: #F59E0B; border-radius: 15px;"
            )
            self.animate_size(134, 74)

        self.bg_frame.update()
        self.update()

    def animate_size(self, w, h):
        self.setMaximumSize(16777215, 16777215)
        self.anim_size.setStartValue(self.size())
        self.anim_size.setEndValue(QSize(w, h))
        self.anim_size.start()

    def update_audio_level(self, rms: float):
        if self.state == BubbleState.RECORDING:
            self.waveform.update_level(rms)

    def update_preview_text(self, text: str):
        if self.state == BubbleState.RECORDING and text:
            import re

            from src.utils.text_cleaner import sanitize_symbol_loops
            text = sanitize_symbol_loops(text)
            if not text or not re.search(r"[a-zA-Z0-9]", text):
                return
            display_text = text[-30:] if len(text) > 30 else text
            self.preview_label.setText(display_text)
            self.preview_label.show()
            new_w = min(374, max(174, 144 + len(display_text) * 7))
            self.animate_size(new_w, 74)
