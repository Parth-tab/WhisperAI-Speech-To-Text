import pytest
from unittest.mock import patch, MagicMock

from src.utils.list_detector import detect_list_intent, detect_list_mode
from src.llm.engine import _ensure_list_newlines


# --- Group 1: detect_list_intent (legacy wrapper) ---

def test_detect_list_intent_with_number_ordinals():
    assert detect_list_intent("number one finish the report number two send the email") is True


def test_detect_list_intent_with_ordinal_words():
    assert detect_list_intent("first update the docs second run the tests") is True


def test_detect_list_intent_with_item_prefix():
    assert detect_list_intent("item one fix the bug item two write tests") is True


def test_detect_list_intent_with_colon_pattern():
    assert detect_list_intent("one: apples two: bananas three: cherries") is True


def test_detect_list_intent_plain_sentence_returns_false():
    assert detect_list_intent("This is a regular sentence with no list.") is False


def test_detect_list_intent_decimal_no_false_positive():
    assert detect_list_intent("The price is $3.50 and version 2.0 is out.") is False


def test_detect_list_intent_version_number_no_false_positive():
    assert detect_list_intent("We need to fix Python 3.10 compatibility.") is False


def test_detect_list_intent_empty_string_returns_false():
    assert detect_list_intent("") is False


def test_detect_list_intent_case_insensitive():
    assert detect_list_intent("FIRST do this SECOND do that") is True


# --- Group 2: detect_list_mode (pure vs mixed vs none) ---

def test_detect_list_mode_pure_list_from_start():
    # Starts directly with ordinal — no prose prefix
    assert detect_list_mode("number one finish the report number two send the email") == 'pure'


def test_detect_list_mode_pure_ordinal_words():
    assert detect_list_mode("first update the docs second run the tests") == 'pure'


def test_detect_list_mode_pure_brief_connector():
    # Very short prefix (< 10 chars) should still be 'pure'
    assert detect_list_mode("OK so first do this") == 'pure'


def test_detect_list_mode_mixed_paragraph_then_list():
    # Substantial prose (>= 10 chars) before the list trigger → 'mixed'
    assert detect_list_mode("The application is performing well. Number one it takes input.") == 'mixed'


def test_detect_list_mode_mixed_longer_prose():
    assert detect_list_mode("This project is going well. Now for action items: first update the docs.") == 'mixed'


def test_detect_list_mode_none_plain_prose():
    assert detect_list_mode("This is a regular sentence with no list.") == 'none'


def test_detect_list_mode_none_decimal_no_false_positive():
    assert detect_list_mode("The price is $3.50 and version 2.0 is out.") == 'none'


def test_detect_list_mode_none_empty():
    assert detect_list_mode("") == 'none'


# --- Group 3: _ensure_list_newlines ---

def test_ensure_list_newlines_pure_collapses_to_separate_lines():
    result = _ensure_list_newlines("1. Apples 2. Bananas 3. Cherries", list_mode='pure')
    assert result == "\n\n1. Apples\n2. Bananas\n3. Cherries"


def test_ensure_list_newlines_pure_already_correct_no_extra_newlines():
    result = _ensure_list_newlines("1. Apples\n2. Bananas\n3. Cherries", list_mode='pure')
    assert result == "\n\n1. Apples\n2. Bananas\n3. Cherries"


def test_ensure_list_newlines_mixed_preserves_prose():
    # In mixed mode: NO leading \n\n — prose comes first
    result = _ensure_list_newlines("The project is going well.\n1. Update docs. 2. Run tests.", list_mode='mixed')
    assert result == "The project is going well.\n1. Update docs.\n2. Run tests."


def test_ensure_list_newlines_none_decimal_unchanged():
    text = "The price is $3.50 and 2.0 is stable."
    assert _ensure_list_newlines(text, list_mode='none') == text


def test_ensure_list_newlines_none_prose_unchanged():
    text = "This is prose. 2. And some more."
    assert _ensure_list_newlines(text, list_mode='none') == text


def test_ensure_list_newlines_pure_empty_input():
    assert _ensure_list_newlines("", list_mode='pure') == "\n\n"


# --- Group 4: Integration — clean_text routes to correct mode ---

@patch('src.utils.list_detector.detect_list_mode', return_value='pure')
@patch('src.llm.engine.Llama')
def test_clean_text_pure_list_mode_enforces_newlines(mock_llama, mock_detect):
    mock_instance = MagicMock()
    mock_instance.return_value = {
        'choices': [{'text': '1. Finish the report. 2. Send the email. 3. Call the client.'}],
        'usage': {'completion_tokens': 20},
    }
    mock_llama.return_value = mock_instance

    from src.llm.engine import LLMEngine
    engine = LLMEngine(model_path="dummy/path")
    result = engine.clean_text(
        "number one finish the report number two send the email number three call the client"
    )

    assert "\n" in result
    assert result.startswith("\n\n1.")


@patch('src.utils.list_detector.detect_list_mode', return_value='mixed')
@patch('src.llm.engine.LLMEngine._clean_text_mixed', return_value='The app works well.\n\n1. Takes input.\n2. Processes audio.')
@patch('src.llm.engine.Llama')
def test_clean_text_mixed_mode_delegates_to_split_pass(mock_llama, mock_mixed, mock_detect):
    mock_instance = MagicMock()
    mock_llama.return_value = mock_instance

    from src.llm.engine import LLMEngine
    engine = LLMEngine(model_path="dummy/path")
    result = engine.clean_text(
        "the app works well number one takes input number two processes audio"
    )

    # Verify mixed mode delegated to the split-pass helper
    mock_mixed.assert_called_once()
    # Result from the helper is passed through
    assert "The app works well." in result
    assert "1." in result
    assert "\n" in result


@patch('src.utils.list_detector.detect_list_mode', return_value='none')
@patch('src.llm.engine.Llama')
def test_clean_text_non_list_mode_no_newline_injection(mock_llama, mock_detect):
    mock_instance = MagicMock()
    mock_instance.return_value = {
        'choices': [{'text': 'The price is $3.50 and version 2.0 is out.'}],
        'usage': {'completion_tokens': 15},
    }
    mock_llama.return_value = mock_instance

    from src.llm.engine import LLMEngine
    engine = LLMEngine(model_path="dummy/path")
    result = engine.clean_text(
        "The price is three fifty and version two point zero is out."
    )

    assert result == "The price is $3.50 and version 2.0 is out."
