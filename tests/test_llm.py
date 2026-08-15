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

@patch("src.llm.engine.Llama")
def test_llm_repetition_aborts_pipeline(mock_llama):
    mock_llama_instance = MagicMock()
    mock_llama.return_value = mock_llama_instance
    
    from src.llm.engine import LLMEngine
    engine = LLMEngine(model_path="dummy/path")
    
    # Text with 6 repeating words (2 trigrams)
    text = "hello world test hello world test"
    result = engine.clean_text(text, context="dummy")
    
    # Should return empty string, NOT the raw text
    assert result == ""


@patch("src.llm.engine.Llama")
def test_clean_text_artifact_stripping(mock_llama):
    mock_llama_instance = MagicMock()
    mock_llama.return_value = mock_llama_instance
    engine = LLMEngine(model_path="dummy/path")

    # Test AI header label & ASCII divider stripping
    mock_llama_instance.return_value = {"choices": [{"text": "AI ----------------------------------"}]}
    res1 = engine.clean_text("some text")
    assert res1 == "some text"  # Fallback to raw input since output was non-alphanumeric junk

    # Test trailing dot loop normalization
    mock_llama_instance.return_value = {"choices": [{"text": "Plus,......."}]}
    res2 = engine.clean_text("Plus")
    assert res2 == "Plus."


def test_execute_command_truncates_oversized_payloads():
    engine = LLMEngine.__new__(LLMEngine)
    mock_llm_func = MagicMock(return_value={"choices": [{"text": "Truncated Result"}]})
    engine.llm = mock_llm_func

    massive_text = "A" * 10000
    massive_context = "B" * 2000
    res = engine.execute_command("summarize", massive_text, context=massive_context)

    assert res == "Truncated Result"
    called_prompt = mock_llm_func.call_args[0][0]
    assert "A" * 4000 in called_prompt
    assert "A" * 4001 not in called_prompt
    assert "B" * 500 in called_prompt
    assert "B" * 501 not in called_prompt


