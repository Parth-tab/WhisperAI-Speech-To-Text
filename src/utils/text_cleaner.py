import re

def pre_filter_text(text: str) -> str:
    """
    Regex-based pre-filter for vocable fillers (um, uh, ah, er) and paralinguistic sounds.
    """
    # Remove filler words (case-insensitive, matching as whole words)
    fillers = [r'\bum\b', r'\buh\b', r'\bah\b', r'\ber\b', r'\bhm\b', r'\bhmm\b']
    pattern = re.compile('|'.join(fillers), flags=re.IGNORECASE)
    cleaned_text = pattern.sub('', text)
    
    # Remove extra spaces left by the replacement
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    return cleaned_text.strip()
