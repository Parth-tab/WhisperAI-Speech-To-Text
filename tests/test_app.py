import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.core.app import WhisperAIApp

@patch('src.core.app.AudioCaptureEngine')
@patch('src.core.app.ASREngine')
@patch('src.core.app.LLMEngine')
@patch('src.core.app.make_listener_from_config')
@patch('src.core.app.WindowDetector')
@patch('src.core.app.ClipboardInjector')
def test_app_initialization(MockInjector, MockWindowDetector, MockMakeListener, 
                          MockLLMEngine, MockASREngine, MockAudioCaptureEngine):
    app = WhisperAIApp()
    
    MockMakeListener.assert_called_once()
    MockWindowDetector.assert_called_once()
    MockInjector.assert_called_once()

    app._load_models()
    
    MockAudioCaptureEngine.assert_called_once()
    MockASREngine.assert_called_once()
    MockLLMEngine.assert_called_once()

@patch('src.core.app.AudioCaptureEngine')
@patch('src.core.app.ASREngine')
@patch('src.core.app.LLMEngine')
@patch('src.core.app.make_listener_from_config')
@patch('src.core.app.WindowDetector')
@patch('src.core.app.ClipboardInjector')
def test_app_hotkey_callbacks(MockInjector, MockWindowDetector, MockMakeListener, 
                              MockLLMEngine, MockASREngine, MockAudioCaptureEngine):
    app = WhisperAIApp()
    app._models_loaded = True
    app.audio_engine = MockAudioCaptureEngine.return_value
    
    app.on_hotkey_press()
    app.audio_engine.start_recording.assert_called_once()
    
    app.on_hotkey_release()
    app.audio_engine.stop_recording.assert_called_once()

@patch('src.core.app.AudioCaptureEngine')
@patch('src.core.app.ASREngine')
@patch('src.core.app.LLMEngine')
@patch('src.core.app.make_listener_from_config')
@patch('src.core.app.WindowDetector')
@patch('src.core.app.ClipboardInjector')
def test_on_recording_stopped(MockInjector, MockWindowDetector, MockMakeListener, 
                              MockLLMEngine, MockASREngine, MockAudioCaptureEngine):
    app = WhisperAIApp()
    app.window_detector.get_context.return_value = "test_context"
    app._models_loaded = True
    app.pipeline = MagicMock()
    app.watchdog = MagicMock()
    
    audio_data = np.array([1, 2, 3], dtype='float32')
    app._on_recording_stopped(audio_data)
    
    task = app.transcription_queue.get()
    np.testing.assert_array_equal(task[0], audio_data)
    assert task[1] == "test_context"

@patch('src.core.app.AudioCaptureEngine')
@patch('src.core.app.ASREngine')
@patch('src.core.app.LLMEngine')
@patch('src.core.app.make_listener_from_config')
@patch('src.core.app.WindowDetector')
@patch('src.core.app.ClipboardInjector')
def test_transcription_worker(MockInjector, MockWindowDetector, MockMakeListener, 
                                 MockLLMEngine, MockASREngine, MockAudioCaptureEngine):
    app = WhisperAIApp()
    app.pipeline = MagicMock()
    app.pipeline.process_audio.return_value = "final_output"
    
    audio_data = np.array([1, 2, 3], dtype='float32')
    app.transcription_queue.put((audio_data, "context"))
    app.transcription_queue.put(None)
    
    app._transcription_worker()
    
    app.pipeline.process_audio.assert_called_once()
    app.injector.inject_text.assert_called_once_with("final_output")

@patch('src.core.app.AudioCaptureEngine')
@patch('src.core.app.ASREngine')
@patch('src.core.app.LLMEngine')
@patch('src.core.app.make_listener_from_config')
@patch('src.core.app.WindowDetector')
@patch('src.core.app.ClipboardInjector')
def test_on_audio_chunk(MockInjector, MockWindowDetector, MockMakeListener, 
                        MockLLMEngine, MockASREngine, MockAudioCaptureEngine):
    app = WhisperAIApp()
    app.window_detector.get_context.return_value = "chunk_context"
    app._models_loaded = True
    app.pipeline = MagicMock()
    app.watchdog = MagicMock()
    
    audio_data = np.array([1, 2], dtype='float32')
    app._on_audio_chunk(audio_data)
    
    task = app.transcription_queue.get()
    np.testing.assert_array_equal(task[0], audio_data)
    assert task[1] == "chunk_context"
