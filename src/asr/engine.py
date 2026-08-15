import logging
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger("whisperai")

# faster-whisper downloads models to a cache dir. We point it to ~/.whisperai/models/whisper
# so models persist across app updates.
_WHISPER_CACHE = str(Path.home() / ".whisperai" / "models" / "whisper")


class ASREngine:
    HALLUCINATION_PHRASES = {
        "thank you",
        "thanks",
        "bye",
        "goodbye",
        "see you",
        "see you next time",
        "what the",
        "you have not",
        "subscribe",
        "like and subscribe",
        "thanks for watching",
        "please subscribe",
        "thank you for watching",
        "the end",
        "you",
        "bye bye",
        "okay",
        "so",
    }

    def __init__(self, model_size: str = "tiny.en", compute_type: str = "default", use_gpu: bool = True, language: str | None = None):
        self.model_size = model_size
        self.compute_type = compute_type
        self.use_gpu = use_gpu
        self.language = language
        self.previous_text = ""
        self.model = None

        import os
        total_cores = os.cpu_count() or 4
        self.cpu_threads = max(2, min(total_cores - 2, 4))

        self._load_model()

    def _load_model(self):
        if self.model_size == "large-v3-turbo":
            model_name_or_id = "Systran/faster-whisper-large-v3-turbo"
        elif self.model_size in ("distil-large-v3", "faster-distil-whisper-large-v3"):
            model_name_or_id = "Systran/faster-distil-whisper-large-v3"
        else:
            model_name_or_id = self.model_size

        if self.use_gpu:
            try:
                target_compute = "int8_float16" if self.compute_type in ("default", "auto") else self.compute_type
                logger.info(f"Initializing WhisperModel ({self.model_size}) on CUDA with compute_type={target_compute}...")
                self.model = WhisperModel(
                    model_name_or_id,
                    device="cuda",
                    device_index=0,
                    compute_type=target_compute,
                    download_root=_WHISPER_CACHE,
                    cpu_threads=self.cpu_threads,
                )
            except Exception as e:
                logger.warning(f"CUDA initialization for Whisper failed ({e}). Falling back to CPU.")

        if self.model is None:
            target_compute = "int8" if self.compute_type in ("default", "auto") else self.compute_type
            logger.info(f"Initializing WhisperModel ({self.model_size}) on CPU with compute_type={target_compute}...")
            self.model = WhisperModel(
                model_name_or_id,
                device="cpu",
                compute_type=target_compute,
                download_root=_WHISPER_CACHE,
                cpu_threads=self.cpu_threads,
            )

    def hibernate(self):
        """Unload Whisper model from RAM during idle periods."""
        if hasattr(self, 'model') and self.model is not None:
            logger.info("[ASREngine] Hibernating: Unloading Whisper model from RAM.")
            del self.model
            self.model = None
            import gc
            gc.collect()

    def wake_up(self):
        """Reload Whisper model into RAM."""
        if getattr(self, 'model', None) is None:
            logger.info("[ASREngine] Waking up: Reloading Whisper model.")
            self._load_model()

    @staticmethod
    def _trim_silence(
        audio: np.ndarray,
        sr: int = 16000,
        threshold_db: float = -40.0,
        frame_ms: int = 30,
    ) -> np.ndarray:
        """Trim leading/trailing silence using energy-based detection."""
        if len(audio) == 0:
            return audio
        frame_len = int(sr * frame_ms / 1000)
        threshold_linear = 10 ** (threshold_db / 20)

        # Find first frame above threshold
        start = -1
        for i in range(0, len(audio) - frame_len, frame_len):
            frame = audio[i : i + frame_len]
            if np.sqrt(np.mean(frame**2)) > threshold_linear:
                start = max(0, i - frame_len)  # Keep one frame of padding
                break

        # If no speech found at all, return empty
        if start == -1:
            return np.array([], dtype=np.float32)

        # Find last frame above threshold
        end = len(audio)
        for i in range(len(audio) - frame_len, 0, -frame_len):
            frame = audio[i : i + frame_len]
            if np.sqrt(np.mean(frame**2)) > threshold_linear:
                end = min(len(audio), i + 2 * frame_len)  # Keep one frame of padding
                break

        if start >= end:
            return np.array([], dtype=np.float32)
        return audio[start:end]

    def _is_hallucination(self, text: str) -> bool:
        """Check if the entire transcription is just a known hallucination."""
        cleaned = text.strip().rstrip(".!?,").strip().lower()
        return cleaned in self.HALLUCINATION_PHRASES

    DOMAIN_PROMPTS = {
        "technical": (
            "The following is a technical dictation about software development, "
            "programming, AI, LLMs, Whisper, Qwen, and system architecture. "
            "It may contain markdown formatting like **bold** and code snippets."
        ),
        "medical": (
            "The following is a clinical medical dictation with patient history, "
            "physical findings, pharmacotherapy, dosages, lab values, and SOAP notes."
        ),
        "legal": (
            "The following is a formal legal dictation with statutory citations, "
            "contractual covenants, defined terms, and jurisprudence."
        ),
        "financial": (
            "The following is a financial dictation with earnings reports, valuation metrics, "
            "percentages, basis points, multiples, and fiscal quarters."
        ),
        "academic": (
            "The following is an academic scientific research dictation with methodology, "
            "statistical notation, and peer-reviewed literature references."
        ),
        "email": (
            "The following is professional email correspondence, meeting notes, and concise communication."
        ),
        "general": (
            "The following is high-quality, well-punctuated dictation with clear grammar."
        ),
    }

    def get_initial_prompt(self, profile_id: str = "general") -> str:
        return self.DOMAIN_PROMPTS.get(profile_id, self.DOMAIN_PROMPTS["general"])

    def transcribe(
        self,
        audio_data: np.ndarray,
        dictionary: list | None = None,
        profile_id: str = "general",
        language: str | None = None,
        rms_min: float = 0.005,
        trim_db: float = -45.0,
    ) -> str:
        """
        Transcribe audio with Silero VAD, profile-aware domain prompts, and multilingual support.
        """
        if len(audio_data) == 0:
            return ""

        import time

        from src.core.telemetry import telemetry

        audio_data = audio_data.astype(np.float32).flatten()

        max_val = np.abs(audio_data).max()
        if max_val > 0:
            audio_data = audio_data / max_val

        rms = np.sqrt(np.mean(audio_data**2))
        if rms < rms_min:
            return ""

        sr = 16000
        audio_data = self._trim_silence(audio_data, sr=sr, threshold_db=trim_db)

        if len(audio_data) < sr * 0.3:
            return ""

        # Add 200ms silence padding to head and tail to prevent Whisper start/end clipping
        pad_samples = int(sr * 0.2)
        silence_pad = np.zeros(pad_samples, dtype=np.float32)
        audio_data = np.concatenate((silence_pad, audio_data, silence_pad))

        start_t = time.time()

        kwargs = {
            "beam_size": 5,
            "condition_on_previous_text": False,
            "no_speech_threshold": 0.5,
            "compression_ratio_threshold": 1.8,
            "temperature": 0.0,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500, speech_pad_ms=400),
            "hallucination_silence_threshold": 1.0,
            "repetition_penalty": 1.5,
            "no_repeat_ngram_size": 3,
            "suppress_tokens": [-1],
            "suppress_blank": True,
        }

        # Language selection: if specific language provided, set it; if None or 'auto', Faster-Whisper auto-detects
        active_lang = language or getattr(self, "language", None)
        if active_lang and active_lang != "auto":
            kwargs["language"] = active_lang

        import inspect
        assert self.model is not None, "ASR Model is not loaded"
        sig_params = inspect.signature(self.model.transcribe).parameters
        if "log_prob_threshold" in sig_params:
            kwargs["log_prob_threshold"] = -0.7
        elif "logprob_threshold" in sig_params:
            kwargs["logprob_threshold"] = -0.7

        domain_prompt = self.get_initial_prompt(profile_id)

        if dictionary:
            initial_prompt = ", ".join(dictionary) + ". " + domain_prompt
        elif getattr(self, "previous_text", None):
            seed_words = " ".join(self.previous_text.split()[-4:])
            initial_prompt = domain_prompt + " " + seed_words
        else:
            initial_prompt = domain_prompt

        if initial_prompt:
            kwargs["initial_prompt"] = initial_prompt

        segments, _ = self.model.transcribe(audio_data, **kwargs)
        unique_segment_texts = []
        last_clean_text = ""
        for segment in segments:
            seg_text = segment.text.strip()
            if seg_text and seg_text.lower() != last_clean_text:
                unique_segment_texts.append(seg_text)
                last_clean_text = seg_text.lower()
        text = " ".join(unique_segment_texts)
        end_t = time.time()

        telemetry.log_transcription_latency(end_t - start_t)

        import re

        from src.utils.text_cleaner import sanitize_symbol_loops

        raw_text = text.strip()

        # Early discard: reject raw ASR output containing massive letter repetitions
        if re.search(r"([a-zA-Z])\1{4,}|0{12,}", raw_text):
            logger.warning(f"ASR discarded (repetition loop, length={len(raw_text)})")
            return ""

        text = sanitize_symbol_loops(raw_text)

        # Discard if output contains no valid word characters, numbers, math, or emoji
        if text and not re.search(r"[\w\$\€\£\¥\+\-\*\/\=\<\>\%\#\@\^\&\|\~\U00010000-\U0010ffff]", text):
            return ""

        # Filter out known hallucination phrases
        if self._is_hallucination(text):
            return ""

        if text:
            self.previous_text = text

        return text

    def transcribe_fast_preview(self, audio: np.ndarray, language: str | None = None) -> str:
        if len(audio) == 0 or self.model is None:
            return ""
        try:
            from src.utils.text_cleaner import sanitize_symbol_loops
            kwargs = {
                "beam_size": 1,
                "vad_filter": False,
                "without_timestamps": True,
            }
            active_lang = language or getattr(self, "language", None)
            if active_lang and active_lang != "auto":
                kwargs["language"] = active_lang

            segments, _ = self.model.transcribe(audio, **kwargs)
            raw_text = " ".join([segment.text.strip() for segment in segments])
            return sanitize_symbol_loops(raw_text)
        except Exception:
            return ""
