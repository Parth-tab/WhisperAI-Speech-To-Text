import numpy as np
from unittest.mock import patch, MagicMock
from src.core.app import WhisperAIApp


@patch("src.core.app.AudioWorker")
@patch("src.core.app.ASREngine")
@patch("src.core.app.LLMEngine")
@patch("src.core.app.make_listener_from_config")
@patch("src.core.app.WindowDetector")
@patch("src.core.app.ClipboardInjector")
def test_app_initialization(
    MockInjector,
    MockWindowDetector,
    MockMakeListener,
    MockLLMEngine,
    MockASREngine,
    MockAudioWorker,
):
    app = WhisperAIApp()

    MockMakeListener.assert_called_once()
    MockWindowDetector.assert_called_once()
    MockInjector.assert_called_once()

    app._load_models()

    MockASREngine.assert_called_once()
    MockLLMEngine.assert_called_once()


@patch("src.core.app.AudioWorker")
@patch("src.core.app.ASREngine")
@patch("src.core.app.LLMEngine")
@patch("src.core.app.make_listener_from_config")
@patch("src.core.app.WindowDetector")
@patch("src.core.app.ClipboardInjector")
def test_app_hotkey_callbacks(
    MockInjector,
    MockWindowDetector,
    MockMakeListener,
    MockLLMEngine,
    MockASREngine,
    MockAudioWorker,
):
    app = WhisperAIApp()
    app._models_loaded = True

    app.handle_hotkey_press()
    MockAudioWorker.assert_called_once()
    MockAudioWorker.return_value.start.assert_called_once()
    
    app.audio_worker = MockAudioWorker.return_value
    app.audio_worker.isRunning.return_value = True

    app.handle_hotkey_release()
    app.audio_worker.stop.assert_called_once()


@patch("src.core.app.AudioWorker")
@patch("src.core.app.ASREngine")
@patch("src.core.app.LLMEngine")
@patch("src.core.app.make_listener_from_config")
@patch("src.core.app.WindowDetector")
@patch("src.core.app.ClipboardInjector")
def test_on_recording_stopped(
    MockInjector,
    MockWindowDetector,
    MockMakeListener,
    MockLLMEngine,
    MockASREngine,
    MockAudioWorker,
):
    app = WhisperAIApp()
    app.window_detector.get_context.return_value = ("test_context", "general", "1234")
    app._models_loaded = True
    app.pipeline = MagicMock()
    app.watchdog = MagicMock()
    app.transcription_queue = MagicMock()

    audio_data = np.array([1, 2, 3], dtype="float32")
    app._on_recording_stopped(audio_data)

    app.transcription_queue.put.assert_called_once()
    task = app.transcription_queue.put.call_args[0][0]
    assert np.array_equal(task[0], audio_data)
    assert task[1] == ("test_context", "general", "1234")


@patch("src.core.app.AudioWorker")
@patch("src.core.app.ASREngine")
@patch("src.core.app.LLMEngine")
@patch("src.core.app.make_listener_from_config")
@patch("src.core.app.WindowDetector")
@patch("src.core.app.ClipboardInjector")
def test_transcription_worker(
    MockInjector,
    MockWindowDetector,
    MockMakeListener,
    MockLLMEngine,
    MockASREngine,
    MockAudioWorker,
):
    app = WhisperAIApp()
    app.pipeline = MagicMock()
    app.pipeline.process_audio.return_value = "final_output"

    audio_data = np.array([1, 2, 3], dtype="float32")
    app.transcription_queue.put(
        (audio_data, ("context", "profile", "123"), app.pipeline)
    )
    app.transcription_queue.put(None)

    app._transcription_worker()

    app.pipeline.process_audio.assert_called_once()
    app.injector.inject_text.assert_called_once_with("final_output")


@patch("src.core.app.AudioWorker")
@patch("src.core.app.ASREngine")
@patch("src.core.app.LLMEngine")
@patch("src.core.app.make_listener_from_config")
@patch("src.core.app.WindowDetector")
@patch("src.core.app.ClipboardInjector")
def test_on_audio_chunk(
    MockInjector,
    MockWindowDetector,
    MockMakeListener,
    MockLLMEngine,
    MockASREngine,
    MockAudioWorker,
):
    app = WhisperAIApp()
    app.window_detector.get_context.return_value = "chunk_context"
    app._models_loaded = True
    app.pipeline = MagicMock()
    app.watchdog = MagicMock()

    audio_data = np.array([1, 2], dtype="float32")
    app._on_audio_chunk(audio_data)

    # It should not put anything into the queue since it's disabled
    assert app.transcription_queue.empty()
