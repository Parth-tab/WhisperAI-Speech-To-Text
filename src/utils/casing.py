import re


def to_camel_case(text: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", text)
    if not words:
        return ""
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def to_snake_case(text: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", text)
    return "_".join(w.lower() for w in words)


def to_pascal_case(text: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", text)
    return "".join(w.capitalize() for w in words)


def to_screaming_snake_case(text: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", text)
    return "_".join(w.upper() for w in words)


def to_kebab_case(text: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", text)
    return "-".join(w.lower() for w in words)


def to_path_case(text: str) -> str:
    # Replace explicit spoken "slash" or spaces with /
    text = re.sub(r"\b(slash|backslash)\b", "/", text, flags=re.IGNORECASE)
    words = [w for w in re.split(r"[\s/]+", text) if w]
    return "/".join(words)


def apply_casing_transforms(text: str) -> str:
    """
    Transforms spoken identifier prefixes into programmatic casing conventions.
    Supported triggers:
      - camel <text> / state <text> -> camelCase
      - snake <text> -> snake_case
      - pascal <text> / component <text> -> PascalCase
      - constant <text> / screaming snake <text> -> SCREAMING_SNAKE_CASE
      - kebab <text> -> kebab-case
      - path <text> -> path/to/file
    """
    if not text:
        return text

    patterns = [
        (r"(?i)\b(?:screaming\s+snake(?:\s+case)?|constant(?:\s+case)?)\s+([a-zA-Z0-9_\s]+?)(?=\s+(?:and|or|then|\.|$)|$)", to_screaming_snake_case),
        (r"(?i)\b(?:camel(?:\s+case)?|state)\s+([a-zA-Z0-9_\s]+?)(?=\s+(?:and|or|then|\.|$)|$)", to_camel_case),
        (r"(?i)\b(?:pascal(?:\s+case)?|component)\s+([a-zA-Z0-9_\s]+?)(?=\s+(?:and|or|then|\.|$)|$)", to_pascal_case),
        (r"(?i)\b(?:snake(?:\s+case)?)\s+([a-zA-Z0-9_\s]+?)(?=\s+(?:and|or|then|\.|$)|$)", to_snake_case),
        (r"(?i)\b(?:kebab(?:\s+case)?)\s+([a-zA-Z0-9_\s]+?)(?=\s+(?:and|or|then|\.|$)|$)", to_kebab_case),
        (r"(?i)\b(?:path(?:\s+case)?)\s+([a-zA-Z0-9_\s/]+?)(?=\s+(?:and|or|then|\.|$)|$)", to_path_case),
    ]

    for pattern, transformer in patterns:
        def repl(match, fn=transformer):
            inner_text = match.group(1).strip()
            return fn(inner_text)

        text = re.sub(pattern, repl, text)

    return text
