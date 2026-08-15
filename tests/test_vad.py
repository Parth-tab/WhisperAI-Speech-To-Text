from unittest.mock import MagicMock, patch

import numpy as np

from src.audio.vad import VADEngine


@patch("src.audio.vad.onnxruntime.InferenceSession")
@patch("src.audio.vad.Path.exists", return_value=True)
def test_vad_initialization(mock_exists, mock_session):
    engine = VADEngine(threshold=0.6, min_silence_duration_ms=800, sample_rate=16000)
    assert engine.threshold == 0.6
    assert engine.min_silence_duration_ms == 800
    assert engine.sample_rate == 16000
    assert engine._state.shape == (2, 1, 128)
    assert engine._speech_detected is False


@patch("src.audio.vad.onnxruntime.InferenceSession")
@patch("src.audio.vad.Path.exists", return_value=True)
def test_vad_chunk_padding_and_truncation(mock_exists, mock_session):
    mock_run = MagicMock()
    mock_run.return_value = (np.array([[0.8]], dtype=np.float32), np.zeros((2, 1, 128), dtype=np.float32))
    mock_session.return_value.run = mock_run

    engine = VADEngine()

    # Chunk < 512 samples
    short_chunk = np.ones(256, dtype=np.float32)
    engine.process_chunk(short_chunk)
    assert mock_run.call_args[0][1]["input"].shape == (1, 512)

    # Chunk > 512 samples
    long_chunk = np.ones(1024, dtype=np.float32)
    engine.process_chunk(long_chunk)
    assert mock_run.call_args[0][1]["input"].shape == (1, 512)


@patch("src.audio.vad.onnxruntime.InferenceSession")
@patch("src.audio.vad.Path.exists", return_value=True)
def test_vad_speech_detection_and_silence_timeout(mock_exists, mock_session):
    engine = VADEngine(threshold=0.5, min_silence_duration_ms=500, sample_rate=16000)

    # 1. Feed speech chunks (prob = 0.9)
    mock_session.return_value.run.return_value = (
        np.array([[0.9]], dtype=np.float32),
        np.zeros((2, 1, 128), dtype=np.float32)
    )

    # Need >= 3 chunks for speech confirmation
    for _ in range(3):
        engine.process_chunk(np.zeros(512, dtype=np.float32))
    assert engine._speech_detected is True

    # Advance duration past 2000ms grace period (2000ms = 32,000 samples = ~63 chunks of 512)
    for _ in range(60):
        engine.process_chunk(np.zeros(512, dtype=np.float32))

    # 2. Now feed silence chunks (prob = 0.1)
    mock_session.return_value.run.return_value = (
        np.array([[0.1]], dtype=np.float32),
        np.zeros((2, 1, 128), dtype=np.float32)
    )

    # 500ms silence = 8,000 samples = ~16 chunks of 512
    triggered = False
    for _ in range(16):
        if engine.process_chunk(np.zeros(512, dtype=np.float32)):
            triggered = True
            break

    assert triggered is True


@patch("src.audio.vad.onnxruntime.InferenceSession")
@patch("src.audio.vad.Path.exists", return_value=True)
def test_vad_grace_period_prevents_early_cutoff(mock_exists, mock_session):
    engine = VADEngine(threshold=0.5, min_silence_duration_ms=200, sample_rate=16000)

    # Pure silence right from the start
    mock_session.return_value.run.return_value = (
        np.array([[0.1]], dtype=np.float32),
        np.zeros((2, 1, 128), dtype=np.float32)
    )

    # Under 2000ms duration (e.g. 10 chunks = 5120 samples = 320ms), must return False
    for _ in range(10):
        result = engine.process_chunk(np.zeros(512, dtype=np.float32))
        assert result is False


@patch("src.audio.vad.onnxruntime.InferenceSession")
@patch("src.audio.vad.Path.exists", return_value=True)
def test_vad_safety_timeout_after_5_minutes(mock_exists, mock_session):
    engine = VADEngine(sample_rate=16000)
    mock_session.return_value.run.return_value = (
        np.array([[0.1]], dtype=np.float32),
        np.zeros((2, 1, 128), dtype=np.float32)
    )

    # Set total frames to > 5 minutes (5 * 60 * 16000 = 4,800,000 samples)
    engine._total_frames = 5_000_000
    engine._speech_detected = False

    result = engine.process_chunk(np.zeros(512, dtype=np.float32))
    assert result is True


@patch("src.audio.vad.onnxruntime.InferenceSession")
@patch("src.audio.vad.Path.exists", return_value=True)
def test_vad_reset_state(mock_exists, mock_session):
    engine = VADEngine()
    engine._silence_frames = 100
    engine._total_frames = 500
    engine._speech_detected = True
    engine._consecutive_speech_chunks = 5

    engine.reset_state()
    assert engine._silence_frames == 0
    assert engine._total_frames == 0
    assert engine._speech_detected is False
    assert engine._consecutive_speech_chunks == 0
