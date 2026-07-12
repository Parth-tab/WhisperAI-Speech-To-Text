import sys
import numpy as np
from pathlib import Path
from faster_whisper import WhisperModel

# faster-whisper downloads models to a cache dir. We point it to ~/.whisperai/models/whisper
# so models persist across app updates.
_WHISPER_CACHE = str(Path.home() / ".whisperai" / "models" / "whisper")


class ASREngine:
    def __init__(self, model_size: str = "small.en", compute_type: str = "default"):
        self.model_size = model_size
        self.compute_type = compute_type
        print(f"[ASREngine] Loading Whisper '{model_size}' model (compute_type={compute_type})...")
        print(f"[ASREngine] Model cache: {_WHISPER_CACHE}")
        # faster-whisper auto-downloads the model to download_root if not present
        self.model = WhisperModel(
            model_size,
            device="auto",
            compute_type=compute_type,
            download_root=_WHISPER_CACHE,
        )
        print(f"[ASREngine] Model loaded successfully.")

    def transcribe(self, audio_data: np.ndarray, dictionary: list[str] = None) -> str:
        """
        Transcribe the given audio numpy array (16kHz, mono, float32).
        Returns the full transcription as a string.
        """
        if len(audio_data) == 0:
            return ""

        import time
        from src.core.telemetry import telemetry

        initial_prompt = "Here is the dictated text:"
        if dictionary:
            initial_prompt += " " + ", ".join(dictionary)
            
        audio_data = audio_data.astype(np.float32).flatten()
        max_val = np.abs(audio_data).max()
        if max_val > 0:
            audio_data = audio_data / max_val

        start_t = time.time()
        segments, info = self.model.transcribe(
            audio_data,
            beam_size=1,
            language="en",
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            initial_prompt=initial_prompt
        )
        text = " ".join([segment.text for segment in segments])
        end_t = time.time()
        
        telemetry.log_transcription_latency(end_t - start_t)
        
        return text.strip()
