import sys
import os

# ---------------------------------------------------------------------------
# PyInstaller frozen-bundle guard — must run before ANY other imports.
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    # 1. Redirect stdout/stderr to a log file so libraries that write to them
    #    (e.g. tqdm, huggingface_hub) don't crash with "NoneType has no write"
    #    when packaged with --noconsole (which sets stdout/stderr to None).
    import pathlib

    _log_dir = pathlib.Path.home() / ".whisperai" / "logs"
    _log_dir.mkdir(parents=True, exist_ok=True)
    _log_file = open(_log_dir / "whisperai.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = _log_file
    sys.stderr = _log_file

    # 2. Silence huggingface_hub / tqdm progress bars entirely — they need a
    #    real TTY to render and will crash on a redirected stream otherwise.
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

    # 3. Patch os.add_dll_directory so llama_cpp doesn't crash when it tries
    #    to add a non-existent path from its __file__ resolution inside _MEIPASS.
    _orig_add_dll_directory = os.add_dll_directory

    def _safe_add_dll_directory(path):
        if not os.path.exists(path):
            return None
        return _orig_add_dll_directory(path)

    os.add_dll_directory = _safe_add_dll_directory

import multiprocessing
from src.core.app import WhisperAIApp

if __name__ == "__main__":
    multiprocessing.freeze_support()

    # Register the AppUserModelID for Windows so the taskbar and thumbnails
    # correctly display the custom window icon instead of the generic executable icon.
    if os.name == "nt":
        try:
            import ctypes

            myappid = "whisperai.desktop.app.1.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = WhisperAIApp()
    app.start()
