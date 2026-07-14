import re

# Ordinal trigger words and number phrases that signal list intent.
# Split into two patterns:
#   _LIST_TRIGGERS_WORD: ordinals that are full words (safe to use \b on both sides)
#   _LIST_TRIGGERS_PUNCT: patterns ending in punctuation (colon/comma), so no trailing \b
_LIST_TRIGGERS_WORD = re.compile(
    r"\b("
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth"
    r"|number\s+one|number\s+two|number\s+three|number\s+four|number\s+five"
    r"|number\s+six|number\s+seven|number\s+eight|number\s+nine|number\s+ten"
    r"|item\s+one|item\s+two|item\s+three"
    r")\b",
    flags=re.IGNORECASE,
)
# Matches "one:", "two,", etc. No trailing \b because [,:] is a non-word char.
_LIST_TRIGGERS_PUNCT = re.compile(
    r"\bone[,:]|\btwo[,:]|\bthree[,:]|\bfour[,:]|\bfive[,:]", flags=re.IGNORECASE
)

# Minimum characters of prose before the first list trigger to classify as "mixed" mode.
# This prevents brief connective phrases like "OK so" from triggering mixed mode.
_PROSE_PREFIX_MIN_CHARS = 10


def detect_list_mode(text: str) -> str:
    """
    Determine the list formatting mode for the given raw transcription.

    Returns one of three string values:
    - 'none':  No list triggers detected — treat as plain prose.
    - 'pure':  A list is detected with no substantial prose prefix.
               The LLM should output a numbered list immediately.
    - 'mixed': A substantial prose paragraph exists BEFORE the first list
               trigger. The raw text must be split at the boundary and each
               part processed separately, because small (1.5B) models will
               collapse the prose into a list item when given LIST MODE.

    This distinction is the core fix for the "paragraph+list" scenario.
    """
    match = _LIST_TRIGGERS_WORD.search(text) or _LIST_TRIGGERS_PUNCT.search(text)
    if not match:
        return "none"

    prose_prefix = text[: match.start()].strip()
    if len(prose_prefix) >= _PROSE_PREFIX_MIN_CHARS:
        return "mixed"
    return "pure"


def get_list_boundary(text: str) -> tuple[str, str]:
    """
    For 'mixed' mode text, split the raw transcription into two parts:
    - prose_part: everything BEFORE the first list trigger
    - list_part:  the first list trigger and everything AFTER it

    Returns (prose_part, list_part).
    If no list trigger is found, returns (text, "").
    """
    match = _LIST_TRIGGERS_WORD.search(text) or _LIST_TRIGGERS_PUNCT.search(text)
    if not match:
        return text, ""
    return text[: match.start()].strip(), text[match.start() :].strip()


def detect_list_intent(text: str) -> bool:
    """
    Legacy wrapper for backward compatibility.
    Returns True if any list trigger is detected (i.e., mode is not 'none').
    """
    return detect_list_mode(text) != "none"
