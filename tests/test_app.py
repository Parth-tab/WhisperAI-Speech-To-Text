import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.core.app import WhisperAIApp

@patch('src.core.app.AudioCaptureEngine')
@patch('src.core.app.ASREngine')
@patch('src.core.app.LLMEngine')
@patch('src.core.app.HotkeyListener')
@patch('src.core.app.WindowDetector')
@patch('src.core.app.ClipboardInjector')
def test_app_initialization(MockInjector, MockWindowDetector, MockHotkeyListener, 
                          MockLLMEngine, MockASREngine, MockAudioCaptureEngine):
    app = WhisperAIApp()
    
    MockAudioCaptureEngine.assert_called_once()
    MockASREngine.assert_called_once()
    MockLLMEngine.assert_called_once()
    MockHotkeyListener.assert_called_once()
    MockWindowDetector.assert_called_once()
    MockInjector.assert_called_once()

    app.hotkey_listener.set_callbacks.assert_called_once()

@patch('src.core.app.AudioCaptureEngine')
@patch('src.core.app.ASREngine')
@patch('src.core.app.LLMEngine')
@patch('src.core.app.HotkeyListener')
@patch('src.core.app.WindowDetector')
@patch('src.core.app.ClipboardInjector')
def test_app_hotkey_callbacks(MockInjector, MockWindowDetector, MockHotkeyListener, 
                              MockLLMEngine, MockASREngine, MockAudioCaptureEngine):
    app = WhisperAIApp()
    
    app.on_hotkey_press()
    app.audio_engine.start_recording.assert_called_once()
    
    app.on_hotkey_release()
    app.audio_engine.stop_recording.assert_called_once()

@patch('src.core.app.threading.Thread')
@patch('src.core.app.AudioCaptureEngine')
@patch('src.core.app.ASREngine')
@patch('src.core.app.LLMEngine')
@patch('src.core.app.HotkeyListener')
@patch('src.core.app.WindowDetector')
@patch('src.core.app.ClipboardInjector')
def test_on_recording_stopped(MockInjector, MockWindowDetector, MockHotkeyListener, 
                              MockLLMEngine, MockASREngine, MockAudioCaptureEngine,
                              MockThread):
    app = WhisperAIApp()
    app.window_detector.get_context.return_value = "test_context"
    
    audio_data = np.array([1, 2, 3], dtype='float32')
    app._on_recording_stopped(audio_data)
    
    MockThread.assert_called_once()
    args, kwargs = MockThread.call_args
    assert kwargs['target'] == app._run_pipeline_and_inject
    assert kwargs['args'][0] is audio_data
    assert kwargs['args'][1] == "test_context"
    MockThread.return_value.start.assert_called_once()

@patch('src.core.app.AudioCaptureEngine')
@patch('src.core.app.ASREngine')
@patch('src.core.app.LLMEngine')
@patch('src.core.app.HotkeyListener')
@patch('src.core.app.WindowDetector')
@patch('src.core.app.ClipboardInjector')
def test_run_pipeline_and_inject(MockInjector, MockWindowDetector, MockHotkeyListener, 
                                 MockLLMEngine, MockASREngine, MockAudioCaptureEngine):
    app = WhisperAIApp()
    app.pipeline = MagicMock()
    app.pipeline.process_audio.return_value = "final_output"
    
    app._run_pipeline_and_inject(np.array([1, 2, 3]), "context")
    
    app.pipeline.process_audio.assert_called_once()
    app.injector.inject_text.assert_called_once_with("final_output")
