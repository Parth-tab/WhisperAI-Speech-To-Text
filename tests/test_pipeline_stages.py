from unittest.mock import patch

import numpy as np

from src.config.manager import ConfigManager
from src.core.pipeline import (
    AIPipeline,
    ASRStage,
    BacktrackStage,
    CodeModeStage,
    CommandModeStage,
    LLMCleanupStage,
    PipelineContext,
    SnippetStage,
)


def test_asr_stage_empty_audio_is_terminal(mock_asr_engine, mock_llm_engine):
    cfg = ConfigManager()
    stage = ASRStage()
    ctx = PipelineContext(audio_data=np.array([], dtype=np.float32), context_str="", profile_id="general", pid=0)
    stage.process(ctx, cfg, mock_asr_engine, mock_llm_engine)
    assert ctx.is_terminal is True
    assert ctx.text == ""


def test_asr_stage_transcribes_and_passes_config(mock_asr_engine, mock_llm_engine):
    cfg = ConfigManager()
    cfg.set("dictionary", ["WhisperAI", "Kubernetes"])
    cfg.set("whisper_mode", True)

    mock_asr_engine.transcribe.return_value = "transcribed speech"
    stage = ASRStage()
    ctx = PipelineContext(audio_data=np.ones(16000, dtype=np.float32), context_str="", profile_id="general", pid=0)

    stage.process(ctx, cfg, mock_asr_engine, mock_llm_engine)
    assert ctx.is_terminal is False
    assert ctx.text == "transcribed speech"
    mock_asr_engine.transcribe.assert_called_once()


def test_snippet_stage_expansion_terminates_pipeline(mock_asr_engine, mock_llm_engine):
    cfg = ConfigManager()
    cfg.set("snippets", {"my email": "user@example.com", "brb": "be right back"})

    stage = SnippetStage()
    ctx = PipelineContext(audio_data=np.array([1.0]), context_str="", profile_id="general", pid=0, text="My Email!")

    stage.process(ctx, cfg, mock_asr_engine, mock_llm_engine)
    assert ctx.is_terminal is True
    assert ctx.text == "user@example.com"


@patch("src.injection.window_detect.WindowDetector.get_active_window_info", return_value=("Doc", "notepad.exe", 100))
@patch("src.injection.window_detect.is_terminal_process", return_value=False)
@patch("src.core.pipeline.pyperclip")
@patch("src.core.pipeline.pyautogui")
def test_command_mode_stage(mock_pyautogui, mock_pyperclip, mock_is_term, mock_win, mock_asr_engine, mock_llm_engine):
    cfg = ConfigManager()
    stage = CommandModeStage()
    ctx = PipelineContext(audio_data=np.array([1.0]), context_str="", profile_id="general", pid=100, text="command make this polite")

    mock_pyperclip.paste.return_value = "give me the files now"
    mock_llm_engine.execute_command.side_effect = None
    mock_llm_engine.execute_command.return_value = "Could you please share the files?"

    stage.process(ctx, cfg, mock_asr_engine, mock_llm_engine)
    assert ctx.is_terminal is True
    assert ctx.text == "Could you please share the files?"


def test_code_mode_stage_applies_syntax_in_technical_profile(mock_asr_engine, mock_llm_engine):
    cfg = ConfigManager()
    stage = CodeModeStage()
    ctx = PipelineContext(audio_data=np.array([1.0]), context_str="", profile_id="technical", pid=0, text="x plus equals five semicolon")

    stage.process(ctx, cfg, mock_asr_engine, mock_llm_engine)
    assert ctx.text == "x += five ;"


def test_backtrack_stage_wraps_corrections(mock_asr_engine, mock_llm_engine):
    cfg = ConfigManager()
    stage = BacktrackStage()
    ctx = PipelineContext(audio_data=np.array([1.0]), context_str="", profile_id="general", pid=0, text="start server actually stop server")

    stage.process(ctx, cfg, mock_asr_engine, mock_llm_engine)
    assert ctx.text == "<original>start server</original> <correction>actually stop server</correction>"


def test_llm_cleanup_stage_fast_path_bypass(mock_asr_engine, mock_llm_engine):
    cfg = ConfigManager()
    stage = LLMCleanupStage()

    # Clean text with proper punctuation and no fillers -> fast path capitalizes first letter and bypasses LLM
    ctx = PipelineContext(audio_data=np.array([1.0]), context_str="", profile_id="general", pid=0, text="hello world.")
    stage.process(ctx, cfg, mock_asr_engine, mock_llm_engine)

    assert ctx.text == "Hello world."
    mock_llm_engine.clean_text.assert_not_called()


def test_ai_pipeline_full_run(virtual_audio_generator, mock_asr_engine, mock_llm_engine):
    audio = virtual_audio_generator(duration_sec=0.5)
    mock_asr_engine.transcribe.return_value = "testing speech pipeline."

    pipeline = AIPipeline(asr_engine=mock_asr_engine, llm_engine=mock_llm_engine)
    result = pipeline.process_audio(audio)

    assert result == "Testing speech pipeline."
