import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.asr.engine import ASREngine

@patch('src.asr.engine.WhisperModel')
def test_asr_engine(mock_whisper_model):
    # Mock the return of transcribe
    mock_model_instance = MagicMock()
    
    mock_segment = MagicMock()
    mock_segment.text = " Hello world."
    
    mock_model_instance.transcribe.return_value = ([mock_segment], None)
    mock_whisper_model.return_value = mock_model_instance
    
    engine = ASREngine()
    audio_data = np.zeros(16000, dtype=np.float32)
    
    result = engine.transcribe(audio_data)
    
    assert result == "Hello world."
    mock_model_instance.transcribe.assert_called_once_with(audio_data, beam_size=5)
