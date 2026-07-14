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
            r"let me rephrase",
        ]
        self.pattern = re.compile(
            r"\b(" + "|".join(self.markers) + r")\b", re.IGNORECASE
        )

    def process(self, text: str) -> str:
        """
        Detects self-corrections in dictation and wraps them in <correction> tags
        to help the LLM understand intent.
        """
        matches = list(self.pattern.finditer(text))
        if not matches:
            return text

        last_match = matches[-1]
        marker = last_match.group(1)

        before = text[: last_match.start()].strip()
        after = text[last_match.end() :].strip()

        if before and after:
            return f"<original>{before}</original> <correction>{marker} {after}</correction>"

        return text


backtrack_detector = BacktrackDetector()
