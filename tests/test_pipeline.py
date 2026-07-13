import pytest
import numpy as np
from unittest.mock import MagicMock
from src.core.pipeline import AIPipeline
from src.asr.engine import ASREngine
from src.llm.engine import LLMEngine

def test_ai_pipeline():
    # Create mocked engines
    mock_asr = MagicMock(spec=ASREngine)
    mock_asr.transcribe.return_value = "uh hello um world"
    
    mock_llm = MagicMock(spec=LLMEngine)
    mock_llm.clean_text.return_value = "Hello world."
    
    pipeline = AIPipeline(asr_engine=mock_asr, llm_engine=mock_llm)
    
    audio_data = np.zeros(16000, dtype=np.float32)
    result = pipeline.process_audio(audio_data, context="context")
    
    assert result == "Hello world."
    mock_asr.transcribe.assert_called_once_with(
        audio_data, 
        dictionary=[],
        whisper_mode=False,
        trim_db=-40.0,
        rms_min=0.01
    )
    
    # pre_filter_text should have removed "uh" and "um"
    mock_llm.clean_text.assert_called_once_with("hello world", "context", "general")
