import sounddevice as sd
import numpy as np
import threading
import collections
from typing import Callable, Optional
from src.audio.vad import VADEngine

class AudioCaptureEngine:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'float32'
    BLOCKSIZE = 512

    def __init__(self, use_vad: bool = True):
        self.use_vad = use_vad
        self.vad_engine = VADEngine(sample_rate=self.SAMPLE_RATE) if use_vad else None
        self.audio_buffer = collections.deque()
        self._stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self.lock = threading.Lock()
        
        self.on_recording_started: Optional[Callable[[], None]] = None
        self.on_audio_level_changed: Optional[Callable[[float], None]] = None
        self.on_recording_stopped: Optional[Callable[[np.ndarray], None]] = None

    def start_recording(self):
        with self.lock:
            if self.is_recording:
                return
                
            self.audio_buffer.clear()
            if self.vad_engine:
                self.vad_engine.reset_state()
                
            self.is_recording = True
            
            self._stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype=self.DTYPE,
                blocksize=self.BLOCKSIZE,
                callback=self._audio_callback
            )
            self._stream.start()
            
            if self.on_recording_started:
                self.on_recording_started()

    def stop_recording(self):
        with self.lock:
            if not self.is_recording:
                return
                
            self.is_recording = False
            
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
                
            if self.on_recording_stopped:
                if self.audio_buffer:
                    full_audio = np.concatenate(self.audio_buffer)
                else:
                    full_audio = np.array([], dtype=self.DTYPE)
                self.on_recording_stopped(full_audio)

    def _audio_callback(self, indata, frames, time_info, status):
        chunk = indata[:, 0].copy()
        self.audio_buffer.append(chunk)
        
        if self.on_audio_level_changed:
            rms = np.sqrt(np.mean(chunk**2))
            self.on_audio_level_changed(float(rms))
            
        if self.use_vad and self.vad_engine:
            timeout_reached = self.vad_engine.process_chunk(chunk)
            if timeout_reached:
                threading.Thread(target=self.stop_recording, daemon=True).start()
