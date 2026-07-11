from pynput import keyboard
k1 = keyboard.KeyCode.from_char('w')
print(f"k1 vk: {getattr(k1, 'vk', None)}")
