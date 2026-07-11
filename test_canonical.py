from pynput import keyboard
listener = keyboard.Listener()
k1 = keyboard.KeyCode.from_char('w')
print(listener.canonical(k1))
