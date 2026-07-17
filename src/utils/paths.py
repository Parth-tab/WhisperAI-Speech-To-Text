import sys
import os

def get_asset_path(relative_path: str) -> str:
    """Get the absolute path to an asset, handling PyInstaller's _MEIPASS."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # Assuming we are running from the workspace root where src/ is
        # relative_path usually starts with 'src/'
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    return os.path.join(base_path, relative_path)
