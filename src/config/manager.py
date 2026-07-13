import os
import json
from pathlib import Path

class ConfigManager:
    DEFAULT_CONFIG = {
        "hotkey": "<ctrl>+<alt>+w",
        "vad_threshold": 0.5,
        "model_selection": "base",
        "dictionary": [],
        "snippets": {},
        "whisper_mode": False,
        "whisper_vad_threshold": 0.2,
        "whisper_trim_db": -55.0,
        "whisper_rms_min": 0.003
    }

    def __init__(self, config_path=None):
        if config_path is None:
            self.config_dir = Path.home() / ".whisperai"
            self.config_path = self.config_dir / "config.json"
        else:
            self.config_path = Path(config_path)
            self.config_dir = self.config_path.parent
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"Error loading config: {e}. Backing up corrupted file.")
                import shutil
                try:
                    shutil.copy(self.config_path, str(self.config_path) + ".corrupt")
                except Exception:
                    pass

    def save(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()
