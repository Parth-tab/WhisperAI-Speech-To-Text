class Formatter:
    def __init__(self):
        pass

    def check_repetition(self, transcript: str):
        words = transcript.split()
        if len(words) >= 6:
            # Check for repeating trigrams
            for i in range(len(words) - 5):
                if words[i : i + 3] == words[i + 3 : i + 6]:
                    raise ValueError("Pipeline aborted: Transcript repeats nonsense.")
        return transcript
