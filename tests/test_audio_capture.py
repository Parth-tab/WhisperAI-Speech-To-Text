import numpy as np
from src.audio.capture import AudioWorker
import time
from unittest.mock import patch, MagicMock

@patch("src.audio.capture.sd.InputStream")
@patch("src.audio.capture.sd.query_devices")
@patch("src.audio.capture.sd.query_hostapis")
@patch("src.audio.capture.ctypes")
def test_audio_capture(mock_ctypes, mock_hostapis, mock_devices, mock_input_stream):
    def mock_query_hostapis(index=None):
        info = {"name": "Windows WASAPI", "default_input_device": 1, "devices": [1]}
        return [info] if index is None else info
        
    mock_hostapis.side_effect = mock_query_hostapis
    mock_devices.return_value = {"default_samplerate": 48000, "max_input_channels": 1, "name": "Test Mic"}
    mock_stream_instance = MagicMock()
    # Mock stream as context manager
    mock_stream_instance.__enter__ = MagicMock(return_value=mock_stream_instance)
    mock_stream_instance.__exit__ = MagicMock(return_value=None)
    mock_input_stream.return_value = mock_stream_instance
    
    worker = AudioWorker(use_vad=False)
    
    captured_audio = None
    started = False

    def on_chunk(chunk):
        nonlocal started
        started = True
        worker.is_recording = False # Break the loop

    def on_stop(audio):
        nonlocal captured_audio
        captured_audio = audio

    worker.audio_chunk_ready.connect(on_chunk)
    worker.recording_stopped.connect(on_stop)

    # Pre-populate the queue so the while loop has data to read immediately
    worker.audio_queue.put(np.zeros((48000, 1), dtype=np.int16))

    # Run the worker synchronously in the main thread for testing
    worker.run()

    assert started
    assert isinstance(captured_audio, np.ndarray)
    assert len(captured_audio) >= 16000
