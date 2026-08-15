import re

THEME_TOKENS: dict[str, dict[str, str]] = {
    "dark": {
        "bg_primary": "#0F172A",
        "bg_secondary": "#1E293B",
        "bg_bubble": "#111111",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "accent_recording": "#EF4444",
        "accent_processing": "#A855F7",
        "accent_idle": "#3B82F6",
        "accent_success": "#22C55E",
        "border_subtle": "#334155",
    },
    "light": {
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F8FAFC",
        "bg_bubble": "#1E293B",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "accent_recording": "#DC2626",
        "accent_processing": "#9333EA",
        "accent_idle": "#2563EB",
        "accent_success": "#16A34A",
        "border_subtle": "#E2E8F0",
    },
}


def compile_qss(qss_template: str, theme: str = "dark") -> str:
    """Preprocess QSS template string by substituting {{token}} placeholders with valid theme colors."""
    if not qss_template:
        return ""

    tokens = THEME_TOKENS.get(theme.lower(), THEME_TOKENS["dark"])
    compiled = qss_template

    for token, color_val in tokens.items():
        pattern = r"\{\{\s*" + token + r"\s*\}\}"
        compiled = re.sub(pattern, color_val, compiled)

    return compiled
