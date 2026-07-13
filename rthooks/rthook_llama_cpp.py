import os
import sys

_orig_add_dll = os.add_dll_directory

def _safe_add_dll(path):
    """
    Patched version of os.add_dll_directory that silently skips
    non-existent paths.  Inside a PyInstaller frozen bundle, llama_cpp
    computes DLL paths from __file__ which may resolve to locations that
    don't exist; without this guard the call raises FileNotFoundError and
    the app never starts.
    """
    if not os.path.exists(path):
        return None
    return _orig_add_dll(path)

os.add_dll_directory = _safe_add_dll
