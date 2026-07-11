from pynput import keyboard
listener = keyboard.Listener()
k1 = keyboard.Key.ctrl_r
print(listener.canonical(k1))
