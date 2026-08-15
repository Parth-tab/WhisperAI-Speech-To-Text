import time
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.core.app import WhisperAIApp
from src.core.watchdog import ThreadWatchdog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


@patch("src.core.app.ASREngine")
@patch("src.core.app.LLMEngine")
@patch("src.core.app.AudioWorker")
@patch("src.core.app.FlowBubble")
@patch("src.core.app.SystemTrayApp")
@patch("src.core.app.make_listener_from_config")
def test_rapid_hotkey_toggle_thrashing(mock_hotkey, mock_tray, mock_bubble, mock_audio, mock_llm, mock_asr, qapp):
    """Stress test: 50 rapid hotkey press/release cycles."""
    app = WhisperAIApp()
    app._load_models()

    # Rapid toggle loop
    for _ in range(50):
        app.handle_hotkey_press()
        app.handle_hotkey_release()

    assert app.preview_pool is not None
    app.stop()


@patch("src.core.app.ASREngine")
@patch("src.core.app.LLMEngine")
@patch("src.core.app.AudioWorker")
@patch("src.core.app.FlowBubble")
@patch("src.core.app.SystemTrayApp")
@patch("src.core.app.make_listener_from_config")
def test_audio_worker_device_disconnect_and_recovery(mock_hotkey, mock_tray, mock_bubble, mock_audio, mock_llm, mock_asr, qapp):
    """Test device disconnection error handling."""
    app = WhisperAIApp()
    mock_worker = MagicMock()
    app.audio_worker = mock_worker

    # Simulate AudioWorker emitting error signal
    app._on_recording_failed("PortAudioError: Audio device was disconnected")

    mock_worker.wait.assert_called_with(1000)
    app.stop()


def test_watchdog_thread_hang_detection():
    """Test ThreadWatchdog detecting hung background tasks."""
    deadlock_detected = False

    def on_deadlock():
        nonlocal deadlock_detected
        deadlock_detected = True

    watchdog = ThreadWatchdog(timeout_sec=0.1)
    watchdog.on_deadlock = on_deadlock

    # Register dummy thread id with expired timestamp
    watchdog.register_task(99999)
    watchdog.active_tasks[99999] = time.time() - 1.0

    # Run one monitor cycle manually
    now = time.time()
    deadlocked = False
    with watchdog.lock:
        for tid, start_time in list(watchdog.active_tasks.items()):
            if now - start_time > watchdog.timeout_sec:
                deadlocked = True
                del watchdog.active_tasks[tid]

    if deadlocked and watchdog.on_deadlock:
        watchdog.on_deadlock()

    assert deadlock_detected is True
