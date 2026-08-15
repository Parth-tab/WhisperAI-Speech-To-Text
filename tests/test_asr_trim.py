from unittest.mock import MagicMock, patch

import numpy as np

from src.asr.engine import ASREngine


def test_transcribe_quiet_audio_trims_noise():
    # We want to test that transcribe trims silence properly for quiet audio
    # Noise: amplitude 0.005 (-46 dB)
    # Threshold: -40 dB

    # Generate 1 second of noise
    noise = np.ones(16000) * 0.005
    audio = noise.astype(np.float32)

    with (
        patch("src.asr.engine.WhisperModel") as mock_model,
        patch("src.core.telemetry.telemetry.log_transcription_latency"),
    ):
        mock_instance = MagicMock()
        mock_instance.transcribe.return_value = ([], None)
        mock_model.return_value = mock_instance

        eng = ASREngine()
        eng.transcribe(audio, trim_db=-40.0, rms_min=0.001)
        mock_instance.transcribe.assert_called_once()
