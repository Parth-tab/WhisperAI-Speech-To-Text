from unittest.mock import patch, MagicMock
from src.llm.engine import LLMEngine


@patch("src.llm.engine.Llama")
def test_llm_engine(mock_llama):
    mock_llama_instance = MagicMock()
    # Llama instance is callable
    mock_llama_instance.return_value = {"choices": [{"text": "Cleaned text."}]}
    mock_llama.return_value = mock_llama_instance

    engine = LLMEngine(model_path="dummy/path")

    result = engine.clean_text("uh Cleaned text.", context="dummy")

    assert result == "Cleaned text."
    assert mock_llama_instance.called


@patch("src.llm.engine.Llama")
def test_execute_command(mock_llama):
    mock_llama_instance = MagicMock()
    mock_llama_instance.return_value = {"choices": [{"text": "Modified text."}]}
    mock_llama.return_value = mock_llama_instance

    engine = LLMEngine(model_path="dummy/path")
    result = engine.execute_command(
        "Make it formal", "Hey there.", context="Business email"
    )

    assert result == "Modified text."
    assert mock_llama_instance.called

def test_ensure_list_newlines_decimals():
    from src.llm.engine import _ensure_list_newlines
    # Should not split decimals
    text = "Section 1.5. hello"
    result = _ensure_list_newlines(text, list_mode="mixed")
    assert result == "Section 1.5. hello"
    
    # Should split numbered lists
    text2 = "Here is a list. 1. Item one 2. Item two"
    result2 = _ensure_list_newlines(text2, list_mode="mixed")
    assert result2 == "Here is a list.\n1. Item one\n2. Item two"
