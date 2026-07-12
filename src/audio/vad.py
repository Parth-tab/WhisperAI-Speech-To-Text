import numpy as np
import onnxruntime
import urllib.request
from pathlib import Path

class VADEngine:
    def __init__(self, threshold: float = 0.3, min_silence_duration_ms: int = 3500, sample_rate: int = 16000):
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
            urllib.request.urlretrieve(url, self.model_path)
            
        self._session = onnxruntime.InferenceSession(str(self.model_path))
        self.reset_state()
        
    def reset_state(self):
        self._silence_frames = 0
        self._state = np.zeros((2, 1, 128)).astype('float32')
        
    def process_chunk(self, audio_chunk: np.ndarray) -> bool:
        if len(audio_chunk) > 512:
            audio_chunk = audio_chunk[:512]
        elif len(audio_chunk) < 512:
            audio_chunk = np.pad(audio_chunk, (0, 512 - len(audio_chunk)))
            
        inputs = {
            'input': audio_chunk.reshape(1, -1).astype(np.float32),
            'state': self._state,
            'sr': np.array(self.sample_rate, dtype=np.int64)
        }
        
        ort_outs = self._session.run(None, inputs)
        speech_prob, self._state = ort_outs[0], ort_outs[1]
        
        is_speech = speech_prob[0][0] > self.threshold
        
        if is_speech:
            self._silence_frames = 0
        else:
            self._silence_frames += len(audio_chunk)
            
        silence_duration_ms = self._silence_frames / self._frames_per_ms
        return silence_duration_ms >= self.min_silence_duration_ms
