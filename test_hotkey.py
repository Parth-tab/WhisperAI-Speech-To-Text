from pynput import keyboard
from src.hotkey.listener import make_listener_from_config
import time

print("Listening for <ctrl>+<alt>+w for 5 seconds...")
listener = make_listener_from_config("<ctrl>+<alt>+w")
listener.set_callbacks(
    lambda: print("PRESSED"),
    lambda: print("RELEASED")
)
listener.start()
time.sleep(5)
print("Done.")
