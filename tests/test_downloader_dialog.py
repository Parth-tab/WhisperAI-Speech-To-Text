from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from src.config.manager import ConfigManager
from src.gui.downloader_dialog import DownloaderDialog, DownloadWorker


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_downloader_dialog_ui_and_progress(qapp):
    cfg = ConfigManager()
    dialog = DownloaderDialog(cfg)

    assert dialog.progress_bar.value() == 0
    assert "Starting download" in dialog.status_label.text()

    # Update progress
    dialog.update_progress(45, "Downloading model weights...")
    assert dialog.progress_bar.value() == 45
    assert dialog.status_label.text() == "Downloading model weights..."

    # Handle error
    dialog.handle_error("Network Timeout")
    assert "Error: Network Timeout" in dialog.status_label.text()
    dialog.close()


@patch("src.llm.engine._ensure_model")
@patch("src.asr.engine.ASREngine")
def test_download_worker_run(mock_asr, mock_llm, qapp):
    cfg = ConfigManager()
    worker = DownloadWorker(cfg)

    progress_updates = []
    worker.progress.connect(lambda pct, msg: progress_updates.append((pct, msg)))

    finished_called = False
    def on_finished():
        nonlocal finished_called
        finished_called = True
    worker.finished.connect(on_finished)

    worker.run()

    assert mock_llm.called
    assert mock_asr.called
    assert finished_called is True
    assert any(pct == 100 for pct, _ in progress_updates)
