from pynput import keyboard
keys = keyboard.HotKey.parse('<ctrl>+<alt>+w')
print(keys)
