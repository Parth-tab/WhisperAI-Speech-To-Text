import re


class Formatter:
    def __init__(self):
        pass

    def check_repetition(self, transcript: str):
        if not transcript:
            return transcript

        # Catch genuine letter loops (5+ identical letters like aaaaaaa) or dot/comma loops (5+)
        if re.search(r"([a-zA-Z])\1{4,}|([.,;:!?])\1{4,}|0{12,}", transcript):
            raise ValueError("Pipeline aborted: Transcript contains repetition loop.")

        words = transcript.split()
        n = len(words)
        if n >= 6:
            # 1. Check for adjacent repeating trigrams
            for i in range(n - 5):
                if words[i : i + 3] == words[i + 3 : i + 6]:
                    raise ValueError("Pipeline aborted: Transcript repeats nonsense.")

            # 2. Check for long-range block repetitions (10+ word sequences appearing multiple times)
            min_ngram = 10
            seen = {}
            for i in range(n - min_ngram + 1):
                ngram = " ".join(words[i : i + min_ngram]).lower()
                if ngram in seen:
                    prev_idx = seen[ngram]
                    if i - prev_idx >= min_ngram:
                        raise ValueError(f"Pipeline aborted: Transcript contains repeating block loop of {min_ngram}+ words.")
                else:
                    seen[ngram] = i
        return transcript
