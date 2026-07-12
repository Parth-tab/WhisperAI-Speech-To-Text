import sounddevice as sd
import numpy as np
import threading
import collections
import queue
import scipy.signal
import scipy.io.wavfile
from typing import Callable, Optional
from src.audio.vad import VADEngine

class AudioCaptureEngine:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'float32'
    BLOCKSIZE = 512
    SILENCE_TIMEOUT_MS = 3500

    def __init__(self, use_vad: bool = True):
        self.use_vad = use_vad
        self.vad_engine = VADEngine(sample_rate=self.SAMPLE_RATE, min_silence_duration_ms=self.SILENCE_TIMEOUT_MS) if use_vad else None
        self.audio_buffer = collections.deque()
        self._stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self.lock = threading.Lock()
        self.vad_queue = queue.Queue()
        self.vad_thread = None
        
        self.on_recording_started: Optional[Callable[[], None]] = None
        self.on_audio_level_changed: Optional[Callable[[float], None]] = None
        self.on_recording_stopped: Optional[Callable[[np.ndarray], None]] = None
        self.on_audio_chunk: Optional[Callable[[np.ndarray], None]] = None
        self._streaming_buffer = []
        self._resample_buffer = np.array([], dtype=self.DTYPE)
        self.chunk_duration = 2.0
        self.chunk_samples = int(self.SAMPLE_RATE * self.chunk_duration)
        self._debug_dumped = False
        self._debug_buffer = []
        
        try:
            device_info = sd.query_devices(sd.default.device[0], 'input')
            self.device_samplerate = int(device_info['default_samplerate'])
            self.device_channels = min(2, int(device_info['max_input_channels']))
        except Exception:
            self.device_samplerate = self.SAMPLE_RATE
            self.device_channels = self.CHANNELS

    def start_recording(self):
        with self.lock:
            if self.is_recording:
                return
                
            self.audio_buffer.clear()
            self._streaming_buffer = []
            self._resample_buffer = np.array([], dtype=self.DTYPE)
            self._debug_dumped = False
            self._debug_buffer = []
            if self.vad_engine:
                self.vad_engine.reset_state()
                while not self.vad_queue.empty():
                    try:
                        self.vad_queue.get_nowait()
                    except queue.Empty:
                        break
                
            self.is_recording = True
            
            if self.vad_engine:
                self.vad_thread = threading.Thread(target=self._vad_worker, daemon=True)
                self.vad_thread.start()
            
            self._stream = sd.InputStream(
                samplerate=self.device_samplerate,
                channels=self.device_channels,
                dtype=self.DTYPE,
                blocksize=0,
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
            
        full_audio = None
        chunk_data = None
        with self.lock:
            if self.audio_buffer:
                full_audio = np.concatenate(list(self.audio_buffer))
            else:
                full_audio = np.array([], dtype=self.DTYPE)
            
            if self._streaming_buffer:
                chunk_data = np.concatenate(self._streaming_buffer)
                
            self._streaming_buffer.clear()
            
        if chunk_data is not None and self.on_audio_chunk:
            self.on_audio_chunk(chunk_data)
            
        if self.on_recording_stopped:
            self.on_recording_stopped(full_audio)

    def _audio_callback(self, indata, frames, time_info, status):
        if indata.shape[1] > 1:
            chunk = np.mean(indata, axis=1, dtype=self.DTYPE)
        else:
            chunk = indata[:, 0].copy()
            
        if self.device_samplerate != self.SAMPLE_RATE:
            num_samples = int(len(chunk) * self.SAMPLE_RATE / self.device_samplerate)
            chunk = scipy.signal.resample(chunk, num_samples).astype(self.DTYPE)
            
        with self.lock:
            if not self._debug_dumped:
                self._debug_buffer.append(chunk)
                if sum(len(c) for c in self._debug_buffer) >= 3 * self.SAMPLE_RATE:
                    debug_audio = np.concatenate(self._debug_buffer)[:3 * self.SAMPLE_RATE]
                    scipy.io.wavfile.write('debug_dump.wav', self.SAMPLE_RATE, debug_audio)
                    self._debug_dumped = True

            self.audio_buffer.append(chunk)
            self._streaming_buffer.append(chunk)
            
            if self.use_vad and self.vad_engine:
                self._resample_buffer = np.concatenate([self._resample_buffer, chunk])
                while len(self._resample_buffer) >= self.BLOCKSIZE:
                    vad_chunk = self._resample_buffer[:self.BLOCKSIZE]
                    self._resample_buffer = self._resample_buffer[self.BLOCKSIZE:]
                    self.vad_queue.put(vad_chunk)
            
            current_len = sum(len(c) for c in self._streaming_buffer)
            chunk_data = None
            if current_len >= self.chunk_samples:
                chunk_data = np.concatenate(self._streaming_buffer)
                self._streaming_buffer.clear()
                
        if chunk_data is not None and self.on_audio_chunk:
            self.on_audio_chunk(chunk_data)
                    
        if self.on_audio_level_changed:
            rms = np.sqrt(np.mean(chunk**2))
            self.on_audio_level_changed(float(rms))

    def _vad_worker(self):
        while self.is_recording:
            try:
                chunk = self.vad_queue.get(timeout=0.1)
                if self.vad_engine and self.is_recording:
                    timeout_reached = self.vad_engine.process_chunk(chunk)
                    if timeout_reached:
                        threading.Thread(target=self.stop_recording, daemon=True).start()
                        break
            except queue.Empty:
                continue
