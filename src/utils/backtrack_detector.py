import re

class BacktrackDetector:
    def __init__(self):
        # Common correction markers
        self.markers = [
            r"actually",
            r"i mean",
            r"wait",
            r"no wait",
            r"no no",
            r"sorry",
            r"scratch that",
            r"let me rephrase"
        ]
        self.pattern = re.compile(r"\b(" + "|".join(self.markers) + r")\b", re.IGNORECASE)

    def process(self, text: str) -> str:
        """
        Detects self-corrections in dictation and wraps them in <correction> tags
        to help the LLM understand intent.
        """
        match = self.pattern.search(text)
        if not match:
            return text
            
        marker = match.group(1)
        # Split into original intent and correction
        parts = self.pattern.split(text, maxsplit=1)
        if len(parts) >= 3:
            before = parts[0].strip()
            marker = parts[1].strip()
            after = parts[2].strip()
            return f"<original>{before}</original> <correction>{marker} {after}</correction>"
            
        return text

backtrack_detector = BacktrackDetector()
