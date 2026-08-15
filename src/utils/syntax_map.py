import re

# Syntax mappings ordered so multi-word operators come BEFORE their single-word components.
# This prevents "plus equals" from being partially matched by "equals" or "plus" first.
SYNTAX_MAPPINGS = [
    # --- Markdown & Document Structures (Top precedence) ---
    (r"\b(?:heading\s+one|h\s+one)\s*", "# "),
    (r"\b(?:heading\s+two|h\s+two)\s*", "## "),
    (r"\b(?:heading\s+three|h\s+three)\s*", "### "),
    (r"\b(?:heading\s+four|h\s+four)\s*", "#### "),
    (r"\b(?:heading\s+five|h\s+five)\s*", "##### "),
    (r"\b(?:heading\s+six|h\s+six)\s*", "###### "),
    (r"\bcode\s+block\b", "```"),
    (r"\b(?:bullet\s+point|bullet)\s*", "- "),
    (r"\b(?:todo\s+checkbox|checkbox\s+item|task\s+item)\s*", "- [ ] "),

    # --- Multi-word / Advanced Code & Systems Operators ---
    (r"\btriple\s+equals\b", "==="),
    (r"\bnot\s+double\s+equals\b", "!=="),
    (r"\bgreater\s+than\s+or\s+equal(\s+to)?\b", ">="),
    (r"\bless\s+than\s+or\s+equal(\s+to)?\b", "<="),
    (r"\bdouble\s+equals\b", "=="),
    (r"\bnot\s+equals(\s+to)?\b", "!="),
    (r"\bplus\s+equals\b", "+="),
    (r"\bminus\s+equals\b", "-="),
    (r"\bfat\s+arrow\b", "=>"),
    (r"\b(arrow|points\s+to)\b", "->"),
    (r"\b(double\s+colon|scope\s+resolution)\b", "::"),
    (r"\b(short\s+declare|walrus\s+operator)\b", ":="),
    (r"\b(channel\s+receive|channel\s+send)\b", "<-"),
    (r"\b(double\s+ampersand|logical\s+and)\b", "&&"),
    (r"\b(double\s+pipe|logical\s+or)\b", "||"),
    (r"\b(nullish\s+coalescing|double\s+question)\b", "??"),
    (r"\boptional\s+chaining\b", "?."),
    (r"\bbitwise\s+left\s+shift\b", "<<"),
    (r"\bbitwise\s+right\s+shift\b", ">>"),
    (r"\bgreater\s+than\b", ">"),
    (r"\bless\s+than\b", "<"),

    # --- Single-word operators ---
    (r"\bequals(\s+to)?\b", "="),
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),

    # --- Delimiters and brackets ---
    (r"\bopen\s+paren(thesis)?\b", "("),
    (r"\bclose\s+paren(thesis)?\b", ")"),
    (r"\bopen\s+bracket\b", "["),
    (r"\bclose\s+bracket\b", "]"),
    (r"\bopen\s+brace\b", "{"),
    (r"\bclose\s+brace\b", "}"),
    (r"\bsemicolon\b", ";"),
    (r"\bcolon\b", ":"),
    (r"\bcomma\b", ","),
    (r"\bdot\b", "."),

    # --- Symbols & Escape Characters ---
    (r"\basterisk\b", "*"),
    (r"\bforward\s+slash\b", "/"),
    (r"\bbackslash\b", r"\\"),
    (r"\bnew\s+line\b", "\n"),
    (r"\bnext\s+line\b", "\n"),
    (r"\bindent\b", "\t"),
    (r"\bdouble\s+quote\b", '"'),
    (r"\bsingle\s+quote\b", "'"),
    (r"\bbacktick\b", "`"),
    (r"\bunderscore\b", "_"),
    (r"\bdash\b", "-"),
    (r"\bampersand\b", "&"),
    (r"\bpipe\b", "|"),

    # --- Legal & Financial Symbols ---
    (r"\bdouble\s+section\s+symbol\b", "§§"),
    (r"\bsection\s+symbol\b", "§"),
    (r"\bparagraph\s+symbol\b", "¶"),
    (r"\bcopyright\s+symbol\b", "©"),
    (r"\bregistered\s+trademark\b", "®"),
    (r"\bbasis\s+points\b", "bps"),

    # --- Academic & LaTeX Symbols ---
    (r"\balpha\b", r"\\alpha"),
    (r"\bbeta\b", r"\\beta"),
    (r"\bgamma\b", r"\\gamma"),
    (r"\bdelta\b", r"\\delta"),
    (r"\btheta\b", r"\\theta"),
    (r"\blambda\b", r"\\lambda"),
    (r"\bsigma\b", r"\\sigma"),
    (r"\bomega\b", r"\\omega"),
    (r"\bsummation\b", r"\\sum"),
    (r"\bintegral\b", r"\\int"),
    (r"\bsquare\s+root\b", r"\\sqrt"),
    (r"\bfraction\b", r"\\frac"),

    # --- Spoken Emojis ---
    (r"\b(rocket\s+emoji|rocket)\b", "🚀"),
    (r"\b(thumbs\s+up\s+emoji|thumbs\s+up)\b", "👍"),
    (r"\b(thumbs\s+down\s+emoji|thumbs\s+down)\b", "👎"),
    (r"\b(fire\s+emoji|fire)\b", "🔥"),
    (r"\b(party\s+popper\s+emoji|party\s+popper)\b", "🎉"),
    (r"\b(check\s+mark\s+emoji|check\s+mark)\b", "✅"),
    (r"\b(cross\s+mark\s+emoji|red\s+x)\b", "❌"),
    (r"\b(eyes\s+emoji|eyes)\b", "👀"),
]


def apply_syntax_map(text: str) -> str:
    """
    Applies deterministic spoken-to-symbol mapping for code, markdown, math, and symbols.
    Uses an ordered list to ensure multi-word operators are matched before single-word components.
    """
    result = text
    for pattern, replacement in SYNTAX_MAPPINGS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result
