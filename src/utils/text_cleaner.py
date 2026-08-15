import re


def deduplicate_repeating_paragraphs(text: str, min_words: int = 6) -> str:
    """Detect and remove duplicate paragraph or multi-sentence blocks."""
    if not text or "\n\n" not in text:
        return text
    paragraphs = text.split("\n\n")
    seen_keys = set()
    unique_paragraphs = []

    for p in paragraphs:
        cleaned_p = p.strip()
        if not cleaned_p:
            continue
        words = cleaned_p.split()
        if len(words) >= min_words:
            key = " ".join(words[:15]).lower()
            if key in seen_keys:
                continue
            seen_keys.add(key)
        unique_paragraphs.append(cleaned_p)

    return "\n\n".join(unique_paragraphs)


def sanitize_symbol_loops(text: str) -> str:
    """
    Universal, character-agnostic sanitizer for trailing/internal symbol loops,
    character-level letter repetitions (kkkkk...), paragraph repetitions, and AI preambles.
    """
    if not text:
        return text

    # Deduplicate repeating paragraph or sentence blocks first
    text = deduplicate_repeating_paragraphs(text)

    # 1. Strip AI / Assistant preamble headers (with or without colons/dashes)
    text = re.sub(r"(?i)^\s*(AI|Assistant)\b\s*[:\-=]*\s*", "", text)
    # 2. Strip Output / Cleaned Text preambles (requiring colons/dashes)
    text = re.sub(r"(?i)^\s*(Output|Cleaned\s*Text)\s*[:\-=]+\s*", "", text)
    # 3. Truncate trailing question mark loops (?????? -> ?)
    text = re.sub(r"\?{2,}$", "?", text)
    # 4. Truncate trailing exclamation mark loops (!!!!!! -> !)
    text = re.sub(r"!{2,}$", "!", text)
    # 5. Truncate trailing sequence of 2+ plain dots or commas (e.g. ..... -> .)
    text = re.sub(r"[\.\…\·,]{2,}$", ".", text).strip()
    # 6. Collapse letter-only character repetitions (3+ like eeeeext -> ext, iiiing -> ing), NEVER digits
    text = re.sub(r"([a-zA-Z])\1{2,}", r"\1", text)
    # 7. Collapse non-code/non-markdown repeating symbols (dots, commas, colons)
    text = re.sub(r"([.,:;])\1{2,}", r"\1", text)
    # 8. Collapse spaced dots (. . . . -> .)
    text = re.sub(r"(\.\s*){2,}", ".", text)
    # 9. Collapse comma-dot loops (,...)
    text = re.sub(r",\s*\.+", ".", text)
    # 10. Strip spaces before trailing sentence punctuation (. ? !)
    text = re.sub(r"\s+([\.\…\·!?])", r"\1", text)

    text = text.strip()

    # 9. Quality gate: Discard if empty or only bare punctuation/spaces without alphanumeric, math, or emoji
    if not text or not re.search(r"[\w\$\€\£\¥\+\-\*\/\=\<\>\%\#\@\^\&\|\~\U00010000-\U0010ffff]", text):
        return ""

    return text


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

    # Apply universal symbol loop sanitizer
    cleaned_text = sanitize_symbol_loops(cleaned_text)

    # Remove extra spaces left by the replacement
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    return cleaned_text.strip()


def needs_llm_cleanup(text: str) -> bool:
    """
    Heuristic check to determine if raw transcription is clean enough to bypass the LLM.
    Returns True if LLM cleanup is needed, False if we should paste raw text instantly.
    """
    if not text or len(text.strip()) < 5:
        return False

    text_lower = text.lower()

    # 1. Check for common filler words/disfluencies
    fillers = ["um", "uh", "er", "ah", "like", "you know", "sort of", "kind of"]
    if any(re.search(r"\b" + filler + r"\b", text_lower) for filler in fillers):
        return True

    # 2. Check for immediate word repetition (e.g., "the the", "I I")
    if re.search(r"\b(\w+)\s+\1\b", text_lower):
        return True

    # 3. Check if it lacks ending punctuation OR markdown formatting
    # If it ends with markdown (like ** or a code block), don't force punctuation
    stripped = text.strip()
    ends_with_punctuation = re.search(r"[.!?]$", stripped)
    ends_with_markdown = re.search(r"[*`]+$", stripped)

    if not ends_with_punctuation and not ends_with_markdown:
        return True

    # 4. Check for symbol loops or messy punctuation
    if re.search(r"([.,!?])\1{1,}", text):
        return True

    # 5. Check for excessive uppercase (shouting / ASR artifact)
    words = stripped.split()
    if len(words) > 3 and sum(1 for w in words if w.isupper()) > len(words) * 0.5:
        return True

    # Text is clean! Bypass LLM.
    return False
