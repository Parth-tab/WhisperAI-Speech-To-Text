from pynput import keyboard
from typing import Callable, Optional


class HotkeyListener:
    """
    Listens for a configurable hold-to-record hotkey combination.
    Default: Right Ctrl held alone (single key, easy to test).
    Can also be configured as a combo like Ctrl+Alt+W.
    """

    def __init__(self, trigger_key=keyboard.Key.ctrl_r, modifier_keys: set = None):
        """
        Args:
            trigger_key: The primary key that triggers recording (e.g. ctrl_r, or KeyCode for 'w').
            modifier_keys: Optional set of modifier keys that must also be held (e.g. {Key.ctrl_l, Key.alt_l}).
        """
        self.trigger_key = trigger_key
        self.modifier_keys: set = modifier_keys or set()

        self.on_press_callback: Optional[Callable[[], None]] = None
        self.on_release_callback: Optional[Callable[[], None]] = None

        self._listener: Optional[keyboard.Listener] = None
        self._currently_held: set = set()
        self._is_recording = False

    def set_callbacks(self, on_press: Callable[[], None], on_release: Callable[[], None]):
        self.on_press_callback = on_press
        self.on_release_callback = on_release

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._currently_held.clear()
        self._is_recording = False

    def _normalise(self, key):
        """Use pynput's built-in canonical mapping to ignore L/R variants and modifier masking."""
        if self._listener:
            return self._listener.canonical(key)
        return key

    def _on_press(self, key):
        norm = self._normalise(key)
        self._currently_held.add(norm)

        # Check if the trigger key is pressed
        norm_trigger = self._normalise(self.trigger_key)
        if norm != norm_trigger:
            return

        # Check all modifiers are held
        norm_mods = {self._normalise(m) for m in self.modifier_keys}
        if not norm_mods.issubset(self._currently_held):
            return

        if not self._is_recording:
            self._is_recording = True
            if self.on_press_callback:
                try:
                    self.on_press_callback()
                except Exception as e:
                    print(f"Error in hotkey press callback: {e}")

    def _on_release(self, key):
        norm = self._normalise(key)
        self._currently_held.discard(norm)

        norm_trigger = self._normalise(self.trigger_key)
        if norm == norm_trigger and self._is_recording:
            self._is_recording = False
            if self.on_release_callback:
                try:
                    self.on_release_callback()
                except Exception as e:
                    print(f"Error in hotkey release callback: {e}")


def make_listener_from_config(hotkey_str: str) -> HotkeyListener:
    """
    Build a HotkeyListener from a config string like '<ctrl>+<alt>+w'.
    Falls back to right-Ctrl-only if parsing fails.
    """
    try:
        parts = [p.strip() for p in hotkey_str.lower().split("+")]
        modifier_keys = set()
        trigger_key = None

        key_map = {
            "<ctrl>": keyboard.Key.ctrl,
            "<alt>": keyboard.Key.alt,
            "<shift>": keyboard.Key.shift,
            "<win>": keyboard.Key.cmd,
        }

        for part in parts:
            if part in key_map:
                modifier_keys.add(key_map[part])
            else:
                # Single character key
                trigger_key = keyboard.KeyCode.from_char(part)

        if trigger_key is None:
            # No regular key found — use right ctrl as sole trigger
            return HotkeyListener(trigger_key=keyboard.Key.ctrl_r)

        # Remove the trigger from modifiers if it ended up there
        modifier_keys.discard(trigger_key)

        return HotkeyListener(trigger_key=trigger_key, modifier_keys=modifier_keys)

    except Exception:
        return HotkeyListener(trigger_key=keyboard.Key.ctrl_r)
