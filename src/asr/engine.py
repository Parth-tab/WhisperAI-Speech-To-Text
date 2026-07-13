import sys
import numpy as np
from pathlib import Path
from faster_whisper import WhisperModel

# faster-whisper downloads models to a cache dir. We point it to ~/.whisperai/models/whisper
# so models persist across app updates.
_WHISPER_CACHE = str(Path.home() / ".whisperai" / "models" / "whisper")


class ASREngine:
    HALLUCINATION_PHRASES = {
        "thank you", "thanks", "bye", "goodbye", "see you", "see you next time",
        "what the", "you have not", "subscribe", "like and subscribe",
        "thanks for watching", "please subscribe", "thank you for watching",
        "the end", "you", "bye bye", "okay", "so",
    }

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

    @staticmethod
    def _trim_silence(audio: np.ndarray, sr: int = 16000, threshold_db: float = -40.0, frame_ms: int = 30) -> np.ndarray:
        """Trim leading/trailing silence using energy-based detection."""
        if len(audio) == 0:
            return audio
        frame_len = int(sr * frame_ms / 1000)
        threshold_linear = 10 ** (threshold_db / 20)

        # Find first frame above threshold
        start = 0
        for i in range(0, len(audio) - frame_len, frame_len):
            frame = audio[i:i+frame_len]
            if np.sqrt(np.mean(frame**2)) > threshold_linear:
                start = max(0, i - frame_len)  # Keep one frame of padding
                break

        # Find last frame above threshold
        end = len(audio)
        for i in range(len(audio) - frame_len, 0, -frame_len):
            frame = audio[i:i+frame_len]
            if np.sqrt(np.mean(frame**2)) > threshold_linear:
                end = min(len(audio), i + 2 * frame_len)  # Keep one frame of padding
                break

        if start >= end:
            return np.array([], dtype=np.float32)
        return audio[start:end]

    def _is_hallucination(self, text: str) -> bool:
        """Check if the entire transcription is just a known hallucination."""
        cleaned = text.strip().rstrip('.!?,').strip().lower()
        if cleaned in self.HALLUCINATION_PHRASES:
            return True
        # Check if it's just repetitions of hallucination phrases
        words = cleaned.split()
        if len(words) <= 4 and cleaned in self.HALLUCINATION_PHRASES:
            return True
        return False

    def transcribe(self, audio_data: np.ndarray, dictionary: list[str] = None) -> str:
        """
        Transcribe the given audio numpy array (16kHz, mono, float32).
        Returns the full transcription as a string.
        """
        if len(audio_data) == 0:
            return ""

        import time
        from src.core.telemetry import telemetry

        initial_prompt = None
        if dictionary:
            initial_prompt = ", ".join(dictionary)
            
        audio_data = audio_data.astype(np.float32).flatten()
        max_val = np.abs(audio_data).max()
        if max_val > 0:
            audio_data = audio_data / max_val

        # Trim leading/trailing silence to reduce hallucinations
        sr = 16000
        audio_data = self._trim_silence(audio_data, sr=sr)

        # Skip if trimmed audio is too short (< 0.3 seconds)
        if len(audio_data) < sr * 0.3:
            return ""

        # Skip if audio is mostly silence (very low RMS)
        rms = np.sqrt(np.mean(audio_data**2))
        if rms < 0.01:
            return ""

        start_t = time.time()
        
        kwargs = {
            "beam_size": 1,
            "language": "en",
            "condition_on_previous_text": False,
            "no_speech_threshold": 0.8,
            "log_prob_threshold": -1.0,
            "temperature": 0.0,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500, speech_pad_ms=400),
        }
        if initial_prompt:
            kwargs["initial_prompt"] = initial_prompt

        segments, info = self.model.transcribe(
            audio_data,
            **kwargs
        )
        text = " ".join([segment.text for segment in segments])
        end_t = time.time()
        
        telemetry.log_transcription_latency(end_t - start_t)
        
        text = text.strip()

        # Filter out known hallucination phrases
        if self._is_hallucination(text):
            return ""

        return text
