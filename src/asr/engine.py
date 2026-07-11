import sys
import numpy as np
from pathlib import Path
from faster_whisper import WhisperModel

# faster-whisper downloads models to a cache dir. We point it to ~/.whisperai/models/whisper
# so models persist across app updates.
_WHISPER_CACHE = str(Path.home() / ".whisperai" / "models" / "whisper")


class ASREngine:
    def __init__(self, model_size: str = "small.en", compute_type: str = "int8"):
        self.model_size = model_size
        self.compute_type = compute_type
        print(f"[ASREngine] Loading Whisper '{model_size}' model (compute_type={compute_type})...")
        print(f"[ASREngine] Model cache: {_WHISPER_CACHE}")
        # faster-whisper auto-downloads the model to download_root if not present
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type=compute_type,
            download_root=_WHISPER_CACHE,
        )
        print(f"[ASREngine] Model loaded successfully.")

    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe the given audio numpy array (16kHz, mono, float32).
        Returns the full transcription as a string.
        """
        if len(audio_data) == 0:
            return ""

        segments, info = self.model.transcribe(
            audio_data,
            beam_size=5,
            language="en",
            condition_on_previous_text=False,
        )
        text = " ".join([segment.text for segment in segments])
        return text.strip()
