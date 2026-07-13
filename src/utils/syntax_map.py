import re

SYNTAX_MAPPINGS = {
    r"\bopen paren(thesis)?\b": "(",
    r"\bclose paren(thesis)?\b": ")",
    r"\bopen bracket\b": "[",
    r"\bclose bracket\b": "]",
    r"\bopen brace\b": "{",
    r"\bclose brace\b": "}",
    r"\bsemicolon\b": ";",
    r"\bcolon\b": ":",
    r"\bcomma\b": ",",
    r"\bperiod\b": ".",
    r"\bdouble equals\b": "==",
    r"\bequals( to)?\b": "=",
    r"\bnot equals( to)?\b": "!=",
    r"\bplus equals\b": "+=",
    r"\bminus equals\b": "-=",
    r"\bplus\b": "+",
    r"\bminus\b": "-",
    r"\basterisk\b": "*",
    r"\bforward slash\b": "/",
    r"\bbackslash\b": "\\",
    r"\bnew line\b": "\n",
    r"\bnext line\b": "\n",
    r"\bindent\b": "\t",
    r"\btab\b": "\t",
    r"\bdouble quote\b": "\"",
    r"\bsingle quote\b": "'",
    r"\bbacktick\b": "`",
    r"\bunderscore\b": "_",
    r"\bdash\b": "-",
    r"\bampersand\b": "&",
    r"\bpipe\b": "|",
    r"\bgreater than( or equal( to)?)?\b": lambda m: ">=" if "equal" in m.group(0) else ">",
    r"\bless than( or equal( to)?)?\b": lambda m: "<=" if "equal" in m.group(0) else "<",
}

def apply_syntax_map(text: str) -> str:
    """
    Applies deterministic spoken-to-symbol mapping for code dictation.
    """
    # Lowercase for robust matching, though we might lose capitalization. 
    # For a syntax map applied BEFORE the LLM, we should probably do case-insensitive regex instead of lowercasing the whole string.
    
    result = text
    for pattern, replacement in SYNTAX_MAPPINGS.items():
        if callable(replacement):
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        else:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            
    # Clean up spaces around certain symbols if needed, but the LLM will also help with formatting.
    return result
