import os
from pathlib import Path
os.environ["HF_HOME"] = str(Path.home() / ".whisperai" / "models")

import sys

# ---------------------------------------------------------------------------
# Failsafes: AVX2 Pre-Flight Checker
# ---------------------------------------------------------------------------
import ctypes
import cpufeature
if not cpufeature.CPUFeature["AVX2"]:
    ctypes.windll.user32.MessageBoxW(0, "Fatal Error: AVX2 instruction set not detected. WhisperAI requires an AVX2 capable CPU.", "Hardware Error", 0)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Global Exception Handler
# ---------------------------------------------------------------------------
def _global_excepthook(exc_type, exc_value, exc_traceback):
    import traceback
    log_dir = Path.home() / ".whisperai" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "whisperai.log", "a", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    error_msg = f"An unexpected error occurred:\n{exc_value}\nCheck logs for details."
    ctypes.windll.user32.MessageBoxW(0, error_msg, "WhisperAI - Crash", 0)
    sys.exit(1)

sys.excepthook = _global_excepthook

# ---------------------------------------------------------------------------
# PyInstaller frozen-bundle guard — must run before ANY other imports.
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    import pathlib

    _log_dir = pathlib.Path.home() / ".whisperai" / "logs"
    _log_dir.mkdir(parents=True, exist_ok=True)
    _log_file = open(_log_dir / "whisperai.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = _log_file
    sys.stderr = _log_file

    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

    _orig_add_dll_directory = os.add_dll_directory

    def _safe_add_dll_directory(path):
        if not os.path.exists(path):
            return None
        return _orig_add_dll_directory(path)

    os.add_dll_directory = _safe_add_dll_directory

import multiprocessing
import logging
from src.core.app import WhisperAIApp

if __name__ == "__main__":
    multiprocessing.freeze_support()

    # Setup logging
    log_dir = Path.home() / ".whisperai" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "whisperai.log"

    logger = logging.getLogger("whisperai")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    # Force third-party root loggers to WARNING
    logging.getLogger().setLevel(logging.WARNING)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.WARNING)

    if os.name == "nt":
        try:
            import ctypes
            myappid = "whisperai.desktop.app.1.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    from src.utils.paths import get_asset_path
    
    logo_png_path = get_asset_path("src/assets/branding/logo.png")
    logo_ico_path = get_asset_path("src/assets/branding/logo.ico")
    
    if not os.path.exists(logo_png_path) or os.path.getsize(logo_png_path) == 0:
        raise RuntimeError(f"Missing or empty branding asset: {logo_png_path}")
    if not os.path.exists(logo_ico_path) or os.path.getsize(logo_ico_path) == 0:
        raise RuntimeError(f"Missing or empty branding asset: {logo_ico_path}")

    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass

    app = WhisperAIApp()
    app.start()
