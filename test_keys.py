from pynput import keyboard
import time

def on_press(key):
    try:
        print(f"PRESS: {key.char} (char)")
    except AttributeError:
        print(f"PRESS: {key} (special)")

def on_release(key):
    try:
        print(f"RELEASE: {key.char} (char)")
    except AttributeError:
        print(f"RELEASE: {key} (special)")

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
time.sleep(8)
listener.stop()
