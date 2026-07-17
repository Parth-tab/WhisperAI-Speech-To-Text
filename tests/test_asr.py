import numpy as np
from unittest.mock import patch, MagicMock
from src.asr.engine import ASREngine


@patch("src.asr.engine.WhisperModel")
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

    assert isinstance(result, str)

@patch("src.asr.engine.WhisperModel")
def test_asr_engine_dsp_logic(mock_whisper_model):
    # Mock the return of transcribe
    mock_model_instance = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = " Testing logic."
    mock_model_instance.transcribe.return_value = ([mock_segment], None)
    mock_whisper_model.return_value = mock_model_instance

    engine = ASREngine()
    
    # 1 second of audio at 16000 sr.
    audio_data = np.zeros(16000, dtype=np.float32)
    # Feed a low-amplitude raw audio pulse (e.g., peak at 0.005)
    audio_data[8000:16000] = 0.005

    # With rms_min=0.01, if normalization doesn't happen before,
    # RMS will be very low (e.g., ~0.0003), and it will return ""
    # With our fix, it normalizes first, max value becomes 1.0, 
    # RMS becomes high enough, and it shouldn't be treated as silence.
    result = engine.transcribe(audio_data, rms_min=0.01)
    
    assert result == "Testing logic."
