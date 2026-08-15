import datetime
from unittest.mock import MagicMock, patch

import numpy as np

from src.asr.engine import ASREngine
from src.core.pipeline import PipelineContext, SnippetStage
from src.injection.injector import ClipboardInjector
from src.injection.window_detect import WindowDetector
from src.llm.style_profiles import get_style_prompt
from src.utils.casing import apply_casing_transforms
from src.utils.syntax_map import apply_syntax_map
from src.utils.text_cleaner import sanitize_symbol_loops


# --- 1. Financial Domain Tests ---
def test_financial_numbers_and_symbols():
    text = "Revenue grew by $1,000,000 representing 888M in total volume"
    cleaned = sanitize_symbol_loops(text)
    assert "$1,000,000" in cleaned
    assert "888M" in cleaned

    macro_text = apply_syntax_map("spread widened by 50 bps in Q3")
    assert "50 bps" in macro_text


# --- 2. Medical & Clinical Domain Tests ---
def test_medical_domain_prompting_and_tags():
    engine = ASREngine.__new__(ASREngine)
    med_prompt = engine.get_initial_prompt("medical")
    assert "clinical medical dictation" in med_prompt
    assert "SOAP" in med_prompt

    style_prompt = get_style_prompt("medical")
    assert "<domain: medical>" in style_prompt
    assert "ISMP_dosages" in style_prompt


# --- 3. Legal & Statutory Domain Tests ---
def test_legal_symbols_and_citations():
    text = apply_syntax_map("pursuant to section symbol 10 and double section symbol 12 paragraph symbol 3")
    assert text == "pursuant to § 10 and §§ 12 ¶ 3"

    style_prompt = get_style_prompt("legal")
    assert "<domain: legal>" in style_prompt
    assert "statutory_citations" in style_prompt


# --- 4. Academic & Scientific LaTeX Tests ---
def test_academic_latex_and_symbols():
    text = apply_syntax_map("integrate alpha plus beta from summation of x")
    assert text == "integrate \\alpha + \\beta from \\sum of x"

    style_prompt = get_style_prompt("academic")
    assert "<domain: academic>" in style_prompt
    assert "LaTeX_math" in style_prompt


# --- 5. Systems, Game Dev & DevOps Casing/Operators ---
def test_spoken_casing_and_systems_operators():
    # Spoken casing transforms
    assert apply_casing_transforms("camel case user auth token") == "userAuthToken"
    assert apply_casing_transforms("snake case database connection pool") == "database_connection_pool"
    assert apply_casing_transforms("pascal case order service client") == "OrderServiceClient"
    assert apply_casing_transforms("constant case max retry count") == "MAX_RETRY_COUNT"
    assert apply_casing_transforms("kebab case api gateway router") == "api-gateway-router"

    # Systems & C++/Rust/Go operators
    assert apply_syntax_map("std double colon vector arrow get size") == "std :: vector -> get size"
    assert apply_syntax_map("ch channel receive data") == "ch <- data"
    assert apply_syntax_map("user short declare new user") == "user := new user"


# --- 6. Markdown & Task Checklist Macros ---
def test_markdown_headers_and_task_lists():
    assert apply_syntax_map("heading one Executive Summary") == "# Executive Summary"
    assert apply_syntax_map("heading two Technical Architecture") == "## Technical Architecture"
    assert apply_syntax_map("heading three Implementation Plan") == "### Implementation Plan"
    assert apply_syntax_map("todo checkbox complete audit checklist") == "- [ ] complete audit checklist"
    assert apply_syntax_map("bullet key takeaway point") == "- key takeaway point"


# --- 7. Multilingual Scripts, Math & Emoji Preservation ---
def test_multilingual_and_emoji_preservation():
    # Chinese, Japanese, Arabic, Russian, Greek, Hindi
    scripts = "你好世界 こんにちは мир العربية ελληνικά नमस्ते"
    assert sanitize_symbol_loops(scripts) == scripts

    # Emojis & Math
    emoji_math = "🚀 Launch status: x = 1, y = 2, total > 100 👍"
    assert sanitize_symbol_loops(emoji_math) == emoji_math


# --- 8. Browser Web-App Tab Context Recognition ---
def test_browser_tab_context_recognition():
    detector = WindowDetector()

    with patch.object(detector, "get_active_window_info", return_value=("PROJ-1024 Fix auth deadlock - Jira - Google Chrome", "chrome.exe", 100)):
        ctx_str, profile_id, _ = detector.get_context()
        assert profile_id == "prd"
        assert "Jira/Linear" in ctx_str

    with patch.object(detector, "get_active_window_info", return_value=("Sprint Planning 2026 - Notion - Microsoft Edge", "msedge.exe", 101)):
        ctx_str, profile_id, _ = detector.get_context()
        assert profile_id == "prd"
        assert "Notion" in ctx_str

    with patch.object(detector, "get_active_window_info", return_value=("Quantum_State_Tomography.tex - Overleaf - Google Chrome", "chrome.exe", 102)):
        ctx_str, profile_id, _ = detector.get_context()
        assert profile_id == "academic"
        assert "Overleaf" in ctx_str

    with patch.object(detector, "get_active_window_info", return_value=("Inbox (3) - user@company.com - Gmail - Brave", "brave.exe", 103)):
        ctx_str, profile_id, _ = detector.get_context()
        assert profile_id == "email"
        assert "Gmail" in ctx_str


# --- 9. Dynamic Snippet Placeholders ({date}, {time}, {clipboard}) ---
def test_dynamic_snippet_placeholders():
    stage = SnippetStage()

    ctx = PipelineContext(audio_data=np.zeros(10), context_str="", profile_id="general", pid=0, text="insert date stamp")

    class DummyConfig:
        def get(self, key, default=None):
            if key == "snippets":
                return {"insert date stamp": "Report {date}"}
            return default

    stage.process(ctx, DummyConfig(), MagicMock(), MagicMock())
    today = datetime.date.today().isoformat()
    assert f"Report {today}" in ctx.text
    assert ctx.is_terminal is True


# --- 10. Multi-Modal Injection Strategy Threshold ---
@patch("src.injection.injector.pyperclip")
@patch("src.injection.injector.pyautogui")
def test_multi_modal_injection_routing(mock_pyautogui, mock_pyperclip):
    injector = ClipboardInjector(prefer_sendinput=True)

    with patch("src.injection.injector.send_unicode_text", return_value=True) as mock_sendinput:
        # Short single-line text -> SendInput
        injector.inject_text("Short single-line text")
        mock_sendinput.assert_called_once_with("Short single-line text")
        mock_pyautogui.hotkey.assert_not_called()

    mock_pyautogui.reset_mock()

    with patch("src.injection.injector.send_unicode_text") as mock_sendinput:
        # Long text (>= 100 chars) -> Clipboard Paste
        long_text = "This is a long multi-sentence paragraph designed to verify that the clipboard paste mechanism is appropriately chosen for large blocks of text exceeding one hundred characters."
        injector.inject_text(long_text)
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "v")
        mock_sendinput.assert_not_called()

    mock_pyautogui.reset_mock()

    with patch("src.injection.injector.send_unicode_text") as mock_sendinput:
        # Multi-line text -> Clipboard Paste
        multiline_text = "Line 1\nLine 2"
        injector.inject_text(multiline_text)
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "v")
        mock_sendinput.assert_not_called()

    mock_pyautogui.reset_mock()

    with patch("src.injection.injector.send_unicode_text") as mock_sendinput:
        # BiDi script (Arabic / Devanagari) -> Forces Clipboard Paste
        bidi_text = "مرحبا بالعالم"
        assert injector.is_bidi_script(bidi_text) is True
        injector.inject_text(bidi_text)
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "v")
        mock_sendinput.assert_not_called()
