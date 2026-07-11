import pytest
from unittest.mock import patch, MagicMock
from src.llm.engine import LLMEngine

@patch('src.llm.engine.Llama')
def test_llm_engine(mock_llama):
    mock_llama_instance = MagicMock()
    # Llama instance is callable
    mock_llama_instance.return_value = {
        'choices': [{'text': 'Cleaned text.'}]
    }
    mock_llama.return_value = mock_llama_instance
    
    engine = LLMEngine(model_path="dummy/path")
    
    result = engine.clean_text("uh Cleaned text.", context="dummy")
    
    assert result == "Cleaned text."
    assert mock_llama_instance.called
