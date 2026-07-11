from pynput import keyboard
from src.hotkey.listener import HotkeyListener

def test_hotkey_listener():
    listener = HotkeyListener(hotkey=keyboard.Key.ctrl_r)
    pressed, released = False, False
    
    def on_press(): nonlocal pressed; pressed = True
    def on_release(): nonlocal released; released = True
        
    listener.set_callbacks(on_press, on_release)
    listener._on_press(keyboard.Key.ctrl_r)
    listener._on_release(keyboard.Key.ctrl_r)
    
    assert pressed and released
