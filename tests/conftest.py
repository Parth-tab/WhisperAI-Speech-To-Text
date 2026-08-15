import pytest
import numpy as np
from unittest.mock import MagicMock


@pytest.fixture
def virtual_audio_generator():
    """Generates synthetic float32 16kHz audio waveforms."""
    def _generator(duration_sec: float = 1.0, freq_hz: float = 440.0, amplitude: float = 0.5):
        sample_rate = 16000
        num_samples = int(sample_rate * duration_sec)
        t = np.linspace(0, duration_sec, num_samples, endpoint=False, dtype=np.float32)
        return (amplitude * np.sin(2 * np.pi * freq_hz * t)).astype(np.float32)
    return _generator


@pytest.fixture
def mock_asr_engine():
    """Mock ASREngine returning configurable transcriptions."""
    mock = MagicMock()
    mock.transcribe.return_value = "Hello world this is a test dictation"
    mock.is_loaded.return_value = True
    return mock


@pytest.fixture
def mock_llm_engine():
    """Mock LLMEngine returning formatted output."""
    mock = MagicMock()
    mock.clean_text.side_effect = lambda text, ctx, profile: text.strip()
    mock.execute_command.side_effect = lambda cmd, sel, ctx: f"Executed: {cmd} on {sel}"
    mock.is_loaded.return_value = True
    return mock
