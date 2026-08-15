STYLE_PROFILES = {
    "general": {
        "name": "General",
        "description": "Standard clean prose, grammatically correct.",
        "prompt_addon": "<domain: general> <rules: clean_grammar, accurate_punctuation, no_preamble>",
    },
    "casual": {
        "name": "Casual",
        "description": "Relaxed and conversational.",
        "prompt_addon": "<domain: casual> <rules: conversational_tone, concise, chat_style, no_preamble>",
    },
    "formal": {
        "name": "Formal",
        "description": "Professional, complete sentences.",
        "prompt_addon": "<domain: formal> <rules: executive_tone, complete_sentences, sophisticated_vocabulary, no_preamble>",
    },
    "technical": {
        "name": "Technical",
        "description": "Code and technical dictation.",
        "prompt_addon": "<domain: technical> <rules: preserve_code_identifiers, casing_conventions, exact_syntax_symbols, docstrings, no_preamble>",
    },
    "email": {
        "name": "Email",
        "description": "Formatted for professional emails.",
        "prompt_addon": "<domain: email> <rules: professional_email_structure, greetings_signoffs, concise_paragraphs, no_preamble>",
    },
    "medical": {
        "name": "Medical / Clinical",
        "description": "Clinical documentation & SOAP notes.",
        "prompt_addon": "<domain: medical> <rules: ISMP_dosages(0.5mg_not_.5mg, 1mg_not_1.0mg), SOAP_structure, pharmacology_RxNorm, plain_text_EHR, no_preamble>",
    },
    "legal": {
        "name": "Legal / Contracts",
        "description": "Legal drafting & statutory citations.",
        "prompt_addon": "<domain: legal> <rules: statutory_citations, Bluebook, capitalize_defined_terms, multi_tier_sections, legal_Latin, no_preamble>",
    },
    "financial": {
        "name": "Financial / Modeling",
        "description": "Financial reports & earnings analysis.",
        "prompt_addon": "<domain: financial> <rules: exact_numbers, negative_parentheses(10M), basis_points_bps, multiples_8.5x, fiscal_quarters_Q1-Q4, no_preamble>",
    },
    "academic": {
        "name": "Academic / Science",
        "description": "Scientific papers & LaTeX notation.",
        "prompt_addon": "<domain: academic> <rules: scientific_methodology, passive_voice, statistical_notation, LaTeX_math, SI_units, no_preamble>",
    },
    "prd": {
        "name": "Product Specs / Jira",
        "description": "PRDs, User stories & Acceptance criteria.",
        "prompt_addon": "<domain: prd> <rules: user_stories, acceptance_criteria_lists, Gherkin_BDD, task_checklists, no_preamble>",
    },
}


def get_style_prompt(profile_id: str) -> str:
    profile = STYLE_PROFILES.get(profile_id, STYLE_PROFILES["general"])
    return profile["prompt_addon"]
