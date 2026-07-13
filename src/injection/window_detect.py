import win32gui
import win32process
import psutil
from typing import Dict

APP_CONTEXT_MAP: Dict[str, str] = {
    "slack.exe": "Slack instant messaging — casual, concise tone",
    "teams.exe": "Microsoft Teams chat — professional but conversational",
    "outlook.exe": "Outlook email — professional, complete sentences",
    "winword.exe": "Microsoft Word — formal document writing",
    "chrome.exe": "Web browser — adapt to content type",
    "msedge.exe": "Web browser — adapt to content type",
    "firefox.exe": "Web browser — adapt to content type",
    "code.exe": "VS Code — technical context, preserve code terms",
    "cursor.exe": "Cursor IDE — technical context, preserve code terms",
    "notepad.exe": "Plain text editor — clean prose",
    "notepad++.exe": "Text editor — clean prose",
}

DEFAULT_CONTEXT = "General text input — use clean, well-formatted prose"

class WindowDetector:
    def __init__(self):
        pass

    def get_active_window_info(self) -> tuple[str, str]:
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd)
            
            process_name = ""
            if pid > 0:
                process = psutil.Process(pid)
                process_name = process.name()
                
            return window_title, process_name
        except Exception:
            return "", ""

    def get_context(self) -> str:
        window_title, process_name = self.get_active_window_info()
        base_context = APP_CONTEXT_MAP.get(process_name.lower(), DEFAULT_CONTEXT)
        return f"{base_context}. Active Window Title: '{window_title}'."
