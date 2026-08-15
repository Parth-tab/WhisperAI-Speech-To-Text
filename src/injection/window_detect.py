import win32gui
import win32process
import psutil
from typing import Dict

APP_CONTEXT_MAP: Dict[str, str] = {
    "slack.exe": "Slack instant messaging — casual, concise tone",
    "discord.exe": "Discord chat — casual, concise, conversational",
    "teams.exe": "Microsoft Teams chat — professional but conversational",
    "outlook.exe": "Outlook email — professional, complete sentences",
    "winword.exe": "Microsoft Word — formal document writing",
    "excel.exe": "Microsoft Excel — financial & tabular data modeling",
    "powerpnt.exe": "Microsoft PowerPoint — executive presentation and slides",
    "chrome.exe": "Web browser — adapt to content type",
    "msedge.exe": "Web browser — adapt to content type",
    "firefox.exe": "Web browser — adapt to content type",
    "brave.exe": "Web browser — adapt to content type",
    "code.exe": "VS Code — technical context, preserve code terms",
    "cursor.exe": "Cursor IDE — technical context, preserve code terms",
    "devenv.exe": "Visual Studio — C++/C# development",
    "unrealeditor.exe": "Unreal Engine Editor — C++ game development",
    "rider64.exe": "JetBrains Rider — .NET and game development",
    "goland64.exe": "GoLand — Go backend development",
    "pycharm64.exe": "PyCharm — Python and data science",
    "obsidian.exe": "Obsidian — markdown knowledge base and notes",
    "figma.exe": "Figma — UI/UX design and design tokens",
    "notepad.exe": "Plain text editor — clean prose",
    "notepad++.exe": "Text editor — clean prose",
}

TERMINAL_PROCESSES = {
    "cmd.exe",
    "powershell.exe",
    "pwsh.exe",
    "windowsterminal.exe",
    "openconsole.exe",
    "bash.exe",
    "mintty.exe",
    "alacritty.exe",
    "wezterm-gui.exe",
}


def is_terminal_process(process_name: str) -> bool:
    """Check if the given process is a command line terminal to prevent sending SIGINT via Ctrl+C."""
    if not process_name:
        return False
    return process_name.lower().strip() in TERMINAL_PROCESSES


DEFAULT_CONTEXT = "General text input — use clean, well-formatted prose"


import re


def _sanitize_window_title(title: str) -> str:
    if not title:
        return ""
    # Strip URLs, paths, and complex query strings
    title = re.sub(r"https?://\S+", "", title)
    title = re.sub(r"[/\\]\S+", "", title)
    # Keep only clean words/numbers (max 30 chars)
    words = re.findall(r"[a-zA-Z0-9]+", title)
    clean_title = " ".join(words[:5])
    return clean_title[:30].strip()


class WindowDetector:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager

    def get_active_window_info(self) -> tuple[str, str, int]:
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd)

            process_name = ""
            if pid > 0:
                process = psutil.Process(pid)
                process_name = process.name()

            return window_title, process_name, pid
        except Exception:
            return "", "", 0

    def get_context(self) -> tuple[str, str, int]:
        window_title, process_name, pid = self.get_active_window_info()
        proc_lower = process_name.lower().strip()
        base_context = APP_CONTEXT_MAP.get(proc_lower, DEFAULT_CONTEXT)
        clean_title = _sanitize_window_title(window_title)

        title_str = f" Target App: '{clean_title}'." if clean_title else ""

        profile_id = "general"
        if self.config_manager:
            app_styles = self.config_manager.get("app_styles", {})
            profile_id = app_styles.get(proc_lower, "general")

        # Browser web-app tab title recognition
        browser_processes = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"}
        if proc_lower in browser_processes and window_title:
            w_lower = window_title.lower()
            if "jira" in w_lower or "linear" in w_lower or "atlassian" in w_lower:
                profile_id = "prd"
                base_context = "Jira/Linear issue tracking — concise user stories and criteria"
            elif "notion" in w_lower:
                profile_id = "prd"
                base_context = "Notion — structured documentation and product specs"
            elif "overleaf" in w_lower or "authorea" in w_lower:
                profile_id = "academic"
                base_context = "Overleaf — LaTeX scientific and academic authoring"
            elif "gmail" in w_lower or "mail.google" in w_lower:
                profile_id = "email"
                base_context = "Gmail web email — professional correspondence"
            elif any(k in w_lower for k in ("colab", "jupyter", "databricks", "snowflake", "kaggle")):
                profile_id = "technical"
                base_context = "Jupyter / Data Science Notebook — code and dataframe expressions"
            elif any(k in w_lower for k in ("zendesk", "intercom", "freshdesk")):
                profile_id = "general"
                base_context = "Customer Support CRM ticket — warm, empathetic assistance"

        return (
            f"{base_context}.{title_str}",
            profile_id,
            pid,
        )
