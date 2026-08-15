import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.audio.wake_word_worker import WakeWordWorker
from src.audio.capture import AudioWorker


def test_wake_word_worker_circular_buffer_and_detection():
    worker = WakeWordWorker(sample_rate=16000, energy_threshold=0.05)
    assert worker.buffer.maxlen == 16000
    assert len(worker.buffer) == 0

    # Add a loud audio burst
    loud_chunk = np.ones(1600, dtype=np.float32) * 0.5
    assert worker._detect_wake_word(loud_chunk) is True

    # Add silent audio
    silent_chunk = np.zeros(1600, dtype=np.float32)
    assert worker._detect_wake_word(silent_chunk) is False

    worker.stop()
    assert worker.running is False


def test_audio_worker_pre_allocated_buffer():
    worker = AudioWorker(use_vad=False)
    assert worker.max_samples == 14400000
    assert worker.write_idx == 0
    assert worker.audio_buffer.shape == (14400000,)


def test_audio_worker_with_preroll_audio():
    preroll = np.ones(16000, dtype=np.float32) * 0.1
    worker = AudioWorker(use_vad=False, preroll_audio=preroll)
    assert worker.write_idx == 16000
    np.testing.assert_allclose(worker.audio_buffer[:16000], preroll)
