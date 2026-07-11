import os
from pathlib import Path

BASE_DIR = Path("E:/WhisperAI")

directories = [
    "src/core",
    "src/audio",
    "src/asr",
    "src/llm",
    "src/injection",
    "src/hotkey",
    "src/gui/widgets",
    "src/config",
    "src/utils",
    "models/whisper",
    "models/llm",
    "resources/icons",
    "resources/sounds",
    "tests",
    "scripts",
    "installer/assets"
]

files = {
    "requirements.txt": """PySide6>=6.7.0
sounddevice>=0.5.0
numpy>=1.26.0
faster-whisper>=1.1.0
onnxruntime>=1.19.0
llama-cpp-python>=0.3.0
pynput>=1.7.0
pywin32>=306
psutil>=6.0.0
pyperclip>=1.9.0
pyautogui>=0.9.54
huggingface-hub>=0.25.0
pyinstaller>=6.10.0
""",
    "src/utils/logger.py": """import logging
import sys

def setup_logger(name="WhisperAI", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

logger = setup_logger()
""",
    "src/hotkey/listener.py": """import threading
from pynput import keyboard
from typing import Callable, Optional

class HotkeyListener:
    def __init__(self, hotkey: keyboard.Key | keyboard.KeyCode = keyboard.Key.ctrl_r):
        self.hotkey = hotkey
        self.on_press_callback: Optional[Callable[[], None]] = None
        self.on_release_callback: Optional[Callable[[], None]] = None
        self._listener: Optional[keyboard.Listener] = None
        self._is_pressed = False

    def set_callbacks(self, on_press: Callable[[], None], on_release: Callable[[], None]):
        self.on_press_callback = on_press
        self.on_release_callback = on_release

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key):
        if key == self.hotkey and not self._is_pressed:
            self._is_pressed = True
            if self.on_press_callback:
                self.on_press_callback()

    def _on_release(self, key):
        if key == self.hotkey and self._is_pressed:
            self._is_pressed = False
            if self.on_release_callback:
                self.on_release_callback()
""",
    "src/injection/window_detect.py": """import win32gui
import win32process
import psutil
from typing import Dict

APP_CONTEXT_MAP: Dict[str, str] = {
    "slack.exe": "Slack instant messaging — casual, concise tone",
    "teams.exe": "Microsoft Teams chat — professional but conversational",
    "outlook.exe": "Outlook email — professional, complete sentences",
    "winword.exe": "Microsoft Word — formal document writing",
    "chrome.exe": "Web browser — adapt to content type",
    "msedge.exe": "Web browser — adapt to content type",
    "firefox.exe": "Web browser — adapt to content type",
    "code.exe": "VS Code — technical context, preserve code terms",
    "cursor.exe": "Cursor IDE — technical context, preserve code terms",
    "notepad.exe": "Plain text editor — clean prose",
    "notepad++.exe": "Text editor — clean prose",
}

DEFAULT_CONTEXT = "General text input — use clean, well-formatted prose"

class WindowDetector:
    def __init__(self):
        pass

    def get_active_window_info(self) -> tuple[str, str]:
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd)
            
            process_name = ""
            if pid > 0:
                process = psutil.Process(pid)
                process_name = process.name()
                
            return window_title, process_name
        except Exception:
            return "", ""

    def get_context(self) -> str:
        _, process_name = self.get_active_window_info()
        return APP_CONTEXT_MAP.get(process_name.lower(), DEFAULT_CONTEXT)
""",
    "src/audio/vad.py": """import numpy as np
import onnxruntime
import urllib.request
from pathlib import Path

class VADEngine:
    def __init__(self, threshold: float = 0.5, min_silence_duration_ms: int = 2000, sample_rate: int = 16000):
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
""",
    "src/audio/capture.py": """import sounddevice as sd
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
        
        self.on_recording_started: Optional[Callable[[], None]] = None
        self.on_audio_level_changed: Optional[Callable[[float], None]] = None
        self.on_recording_stopped: Optional[Callable[[np.ndarray], None]] = None

    def start_recording(self):
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
                threading.Thread(target=self.stop_recording).start()
""",
    "tests/test_hotkey_listener.py": """from pynput import keyboard
from src.hotkey.listener import HotkeyListener

def test_hotkey_listener():
    listener = HotkeyListener(hotkey=keyboard.Key.ctrl_r)
    pressed, released = False, False
    
    def on_press(): nonlocal pressed; pressed = True
    def on_release(): nonlocal released; released = True
        
    listener.set_callbacks(on_press, on_release)
    listener._on_press(keyboard.Key.ctrl_r)
    listener._on_release(keyboard.Key.ctrl_r)
    
    assert pressed and released
""",
    "tests/test_window_detect.py": """from src.injection.window_detect import WindowDetector

def test_window_detector():
    detector = WindowDetector()
    title, process = detector.get_active_window_info()
    
    assert isinstance(title, str)
    assert isinstance(process, str)
    
    context = detector.get_context()
    assert isinstance(context, str) and len(context) > 0
""",
    "tests/test_audio_capture.py": """import numpy as np
from src.audio.capture import AudioCaptureEngine
import time

def test_audio_capture():
    engine = AudioCaptureEngine(use_vad=False)
    started, stopped = False, False
    captured_audio = None
    
    def on_start(): nonlocal started; started = True
    def on_stop(audio): nonlocal stopped, captured_audio; stopped = True; captured_audio = audio
        
    engine.on_recording_started = on_start
    engine.on_recording_stopped = on_stop
    
    engine.start_recording()
    time.sleep(0.5)
    engine.stop_recording()
    
    assert started and stopped
    assert isinstance(captured_audio, np.ndarray) and len(captured_audio) > 0
"""
}

# Add blank __init__.py files
init_dirs = [
    "src", "src/core", "src/audio", "src/asr", "src/llm", "src/injection", 
    "src/hotkey", "src/gui", "src/gui/widgets", "src/config", "src/utils", "tests"
]
for d in init_dirs:
    files[f"{d}/__init__.py"] = ""

def run():
    print(f"Scaffolding WhisperAI at {BASE_DIR}...")
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    for d in directories:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)
        
    for file_path, content in files.items():
        full_path = BASE_DIR / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    print("Phase 1 Scaffolding Complete!")

if __name__ == "__main__":
    run()
