import re

def pre_filter_text(text: str) -> str:
    """
    Regex-based pre-filter for vocable fillers (um, uh, ah, er) and paralinguistic sounds.
    Uses explicit disfluency tokens logic.
    """
    # Remove filler words (case-insensitive, matching as whole words)
    fillers = [r'\bum\b', r'\buh\b', r'\bah\b', r'\ber\b', r'\bhm\b', r'\bhmm\b', r'\blike\b', r'\byou know\b', r'\bbasically\b']
    pattern = re.compile('|'.join(fillers), flags=re.IGNORECASE)
    
    # Introduce explicit disfluency tokens
    text_with_tokens = pattern.sub('<disfluency>', text)
    
    # Selectively omit tokens downstream for "intended" (canonical) text
    cleaned_text = text_with_tokens.replace('<disfluency>', '')
    
    # Remove common ASR hallucination suffixes/prefixes
    hallucination_patterns = [
        r'\bthank you\.?\s*$',
        r'\bbye\.?\s*$', 
        r'\bgoodbye\.?\s*$',
        r'\bsee you\.?\s*$',
        r'\bsee you next time\.?\s*$',
        r'\byou have not\.?\s*$',
        r'\bwhat the\.?\s*$',
        r'^\s*thank you\.?\s*',
        r'^\s*bye\.?\s*',
        r'^\s*okay\.?\s*(?=\w)',
    ]
    for pattern in hallucination_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # Remove extra spaces left by the replacement
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    return cleaned_text.strip()
