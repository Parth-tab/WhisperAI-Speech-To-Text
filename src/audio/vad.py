import numpy as np
import onnxruntime
import urllib.request
import scipy.io.wavfile
from pathlib import Path

DEBUG_BYPASS_VAD = False


class VADEngine:
    def __init__(
        self,
        threshold: float = 0.5,
        min_silence_duration_ms: int = 4000,
        sample_rate: int = 16000,
    ):
        self.threshold = threshold
        self.min_silence_duration_ms = min_silence_duration_ms
        self.sample_rate = sample_rate
        self.model_path = Path.home() / ".whisperai" / "models" / "silero_vad.onnx"
        self._session = None
        self._silence_frames = 0
        self._frames_per_ms = sample_rate / 1000.0
        self._state = None
        self._init_model()

    def _init_model(self):
        if not self.model_path.exists():
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            url = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
            tmp_path = self.model_path.with_suffix(".tmp")
            try:
                urllib.request.urlretrieve(url, tmp_path)
                if tmp_path.stat().st_size > 100000:  # sanity check
                    tmp_path.rename(self.model_path)
                else:
                    raise Exception("Downloaded model file is too small.")
            except Exception as e:
                if tmp_path.exists():
                    tmp_path.unlink()
                raise e

        self._session = onnxruntime.InferenceSession(str(self.model_path))
        self.reset_state()

    def reset_state(self):
        self._silence_frames = 0
        self._total_frames = 0
        self._speech_detected = False
        self._consecutive_speech_chunks = 0
        self._state = np.zeros((2, 1, 128)).astype("float32")
        if hasattr(self, "_debug_chunks"):
            self._debug_chunks = []

    def process_chunk(self, audio_chunk: np.ndarray) -> bool:
        if DEBUG_BYPASS_VAD:
            if not hasattr(self, "_debug_chunks"):
                self._debug_chunks = []
            self._debug_chunks.append(audio_chunk.copy())
            total_samples = sum(len(c) for c in self._debug_chunks)
            if total_samples >= 5 * self.sample_rate:
                full_audio = np.concatenate(self._debug_chunks)
                # Keep exactly 5 seconds
                full_audio = full_audio[: int(5 * self.sample_rate)]
                debug_path = Path.home() / ".whisperai" / "debug_dump.wav"
                scipy.io.wavfile.write(str(debug_path), self.sample_rate, full_audio)
                return True
            return False

        if len(audio_chunk) > 512:
            audio_chunk = audio_chunk[:512]
        elif len(audio_chunk) < 512:
            audio_chunk = np.pad(audio_chunk, (0, 512 - len(audio_chunk)))

        inputs = {
            "input": audio_chunk.reshape(1, -1).astype(np.float32),
            "state": self._state,
            "sr": np.array(self.sample_rate, dtype=np.int64),
        }

        ort_outs = self._session.run(None, inputs)
        speech_prob, self._state = ort_outs[0], ort_outs[1]

        is_speech = speech_prob[0][0] > self.threshold
        self._total_frames += len(audio_chunk)

        if is_speech:
            self._silence_frames = 0
            self._consecutive_speech_chunks += 1
            if self._consecutive_speech_chunks >= 3:
                self._speech_detected = True
        else:
            self._consecutive_speech_chunks = 0
            self._silence_frames += len(audio_chunk)

        # Grace period: don't trigger timeout in the first 2.0 seconds
        total_duration_ms = self._total_frames / self._frames_per_ms
        if total_duration_ms < 2000:
            return False

        # Only trigger silence timeout if speech was actually detected at some point
        if not self._speech_detected:
            # Safety limit: force timeout after 5 minutes if no speech is detected
            if total_duration_ms > 300000:
                return True
            return False

        silence_duration_ms = self._silence_frames / self._frames_per_ms
        return silence_duration_ms >= self.min_silence_duration_ms
