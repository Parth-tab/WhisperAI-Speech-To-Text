import re

# Syntax mappings ordered so multi-word operators come BEFORE their single-word components.
# This prevents "plus equals" from being partially matched by "equals" or "plus" first.
SYNTAX_MAPPINGS = [
    # Multi-word operators FIRST (longest match wins)
    (r"\bgreater than or equal( to)?\b", ">="),
    (r"\bless than or equal( to)?\b", "<="),
    (r"\bdouble equals\b", "=="),
    (r"\bnot equals( to)?\b", "!="),
    (r"\bplus equals\b", "+="),
    (r"\bminus equals\b", "-="),
    (r"\bgreater than\b", ">"),
    (r"\bless than\b", "<"),
    # Single-word operators AFTER
    (r"\bequals( to)?\b", "="),
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    # Delimiters and brackets
    (r"\bopen paren(thesis)?\b", "("),
    (r"\bclose paren(thesis)?\b", ")"),
    (r"\bopen bracket\b", "["),
    (r"\bclose bracket\b", "]"),
    (r"\bopen brace\b", "{"),
    (r"\bclose brace\b", "}"),
    (r"\bsemicolon\b", ";"),
    (r"\bcolon\b", ":"),
    (r"\bcomma\b", ","),
    (r"\bdot\b", "."),
    # Symbols
    (r"\basterisk\b", "*"),
    (r"\bforward slash\b", "/"),
    (r"\bbackslash\b", "\\"),
    (r"\bnew line\b", "\n"),
    (r"\bnext line\b", "\n"),
    (r"\bindent\b", "\t"),
    (r"\bdouble quote\b", '"'),
    (r"\bsingle quote\b", "'"),
    (r"\bbacktick\b", "`"),
    (r"\bunderscore\b", "_"),
    (r"\bdash\b", "-"),
    (r"\bampersand\b", "&"),
    (r"\bpipe\b", "|"),
]


def apply_syntax_map(text: str) -> str:
    """
    Applies deterministic spoken-to-symbol mapping for code dictation.
    Uses an ordered list (not a dict) to ensure multi-word operators
    are matched before their single-word components.
    """
    result = text
    for pattern, replacement in SYNTAX_MAPPINGS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result
