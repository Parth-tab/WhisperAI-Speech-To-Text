import numpy as np
from src.audio.capture import AudioCaptureEngine
import time


def test_audio_capture():
    engine = AudioCaptureEngine(use_vad=False)
    started, stopped = False, False
    captured_audio = None

    def on_start():
        nonlocal started
        started = True

    def on_stop(audio):
        nonlocal stopped, captured_audio
        stopped = True
        captured_audio = audio

    engine.on_recording_started = on_start
    engine.on_recording_stopped = on_stop

    engine.start_recording()
    time.sleep(0.5)
    engine.stop_recording()

    assert started and stopped
    assert isinstance(captured_audio, np.ndarray)
