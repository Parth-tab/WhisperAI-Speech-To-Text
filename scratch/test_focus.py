import sys
import ctypes
from ctypes import wintypes
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer

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
    else:
        print("Failed to get window long")

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(200, 50)
        
        l = QLabel("Click me! I shouldn't steal focus.", self)
        l.setStyleSheet("background-color: red; color: white; border-radius: 10px; padding: 10px;")
        l.move(10, 10)
        
    def showEvent(self, event):
        super().showEvent(event)
        hwnd = self.winId()
        # self.winId() might return an integer or PyCObject. In PySide6 it's an int.
        set_no_activate(int(hwnd))
        
    def mousePressEvent(self, event):
        print("Mouse pressed!")
        super().mousePressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = TestWindow()
    w.show()
    QTimer.singleShot(2000, app.quit) # Exit after 2 seconds for test
    sys.exit(app.exec())
