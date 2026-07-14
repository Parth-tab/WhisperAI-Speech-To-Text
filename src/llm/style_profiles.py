# src/llm/style_profiles.py

STYLE_PROFILES = {
    "general": {
        "name": "General",
        "description": "Standard clean prose, grammatically correct.",
        "prompt_addon": "",
    },
    "casual": {
        "name": "Casual",
        "description": "Relaxed and conversational.",
        "prompt_addon": "Maintain a casual, friendly, and conversational tone. Do not make it overly formal.",
    },
    "formal": {
        "name": "Formal",
        "description": "Professional, complete sentences.",
        "prompt_addon": "Ensure the tone is highly professional, formal, and uses complete sentences.",
    },
    "technical": {
        "name": "Technical",
        "description": "Code and technical dictation.",
        "prompt_addon": "This is a technical/code context. Preserve all technical jargon and exact formatting. Convert natural language descriptions of code into correct syntax (e.g., symbols, indentations) where appropriate.",
    },
    "email": {
        "name": "Email",
        "description": "Formatted for professional emails.",
        "prompt_addon": "Format the output suitable for a professional email. Use standard professional greetings or sign-offs if implied.",
    },
}


def get_style_prompt(profile_id: str) -> str:
    profile = STYLE_PROFILES.get(profile_id, STYLE_PROFILES["general"])
    return profile["prompt_addon"]
