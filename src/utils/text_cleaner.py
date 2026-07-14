import re


def pre_filter_text(text: str) -> str:
    """
    Regex-based pre-filter for vocable fillers and paralinguistic sounds.
    Only strips unambiguous filler words that are NEVER used legitimately.
    Words like 'like', 'you know', 'actually' are left for the LLM's semantic judgment.
    """
    # Only strip unambiguous fillers — NOT 'like', 'you know', 'basically', 'er'
    fillers = [r"\bum\b", r"\buh\b", r"\bah\b", r"\bhm\b", r"\bhmm\b"]
    filler_pattern = re.compile("|".join(fillers), flags=re.IGNORECASE)

    # Single-pass removal (no intermediate <disfluency> tokens — they were never used downstream)
    cleaned_text = filler_pattern.sub("", text)

    # Remove common ASR hallucination suffixes/prefixes
    hallucination_patterns = [
        r"\bthank you\.?\s*$",
        r"\bbye\.?\s*$",
        r"\bgoodbye\.?\s*$",
        r"\bsee you\.?\s*$",
        r"\bsee you next time\.?\s*$",
        r"\byou have not\.?\s*$",
        r"\bwhat the\.?\s*$",
        r"^\s*thank you\.?\s*",
        r"^\s*bye\.?\s*",
    ]
    for h_pattern in hallucination_patterns:
        cleaned_text = re.sub(h_pattern, "", cleaned_text, flags=re.IGNORECASE)

    # Remove extra spaces left by the replacement
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    return cleaned_text.strip()
