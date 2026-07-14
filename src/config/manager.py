import os
import json
import tempfile
import threading
import copy
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
        "whisper_rms_min": 0.003,
    }

    def __init__(self, config_path=None):
        if config_path is None:
            self.config_dir = Path.home() / ".whisperai"
            self.config_path = self.config_dir / "config.json"
        else:
            self.config_path = Path(config_path)
            self.config_dir = self.config_path.parent
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        self._lock = threading.RLock()
        self.load()

    def load(self):
        with self._lock:
            if self.config_path.exists():
                try:
                    with open(self.config_path, "r") as f:
                        data = json.load(f)
                        self.config.update(data)
                except Exception as e:
                    print(f"Error loading config: {e}. Backing up corrupted file.")
                    import shutil

                    try:
                        shutil.copy(
                            self.config_path, str(self.config_path) + ".corrupt"
                        )
                    except Exception:
                        pass

    def save(self):
        with self._lock:
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                fd, tmp_path = tempfile.mkstemp(dir=self.config_dir, suffix=".tmp")
                with os.fdopen(fd, "w") as f:
                    json.dump(self.config, f, indent=4)
                os.replace(tmp_path, self.config_path)  # atomic on Windows NTFS
            except Exception as e:
                print(f"Error saving config: {e}")

    def get(self, key, default=None):
        with self._lock:
            return self.config.get(key, default)

    def set(self, key, value):
        with self._lock:
            self.config[key] = value
            self.save()
