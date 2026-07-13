import re
from src.utils.file_index import file_indexer

class IDEBridge:
    def __init__(self):
        pass

    def process_file_tags(self, text: str, pid: int) -> str:
        if pid <= 0:
            return text
            
        workspace_path = file_indexer.get_workspace_for_pid(pid)
        if not workspace_path:
            return text
            
        # Look for phrases like "at file main" or "in file app" or "@file pipeline"
        # We'll use a regex to capture the file name hint
        pattern = r"\b(?:at file|in file|file) (\w+)\b"
        
        def replacer(match):
            hint = match.group(1)
            found_file = file_indexer.fuzzy_find_file(workspace_path, hint)
            if found_file:
                # Use @filename syntax which is common for AI IDEs like Cursor
                return f"@{found_file}"
            return match.group(0) # Unchanged if not found
            
        result = re.sub(pattern, replacer, text, flags=re.IGNORECASE)
        return result

ide_bridge = IDEBridge()
