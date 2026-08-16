from unittest.mock import MagicMock, patch

import pytest
import requests
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


def test_downloader_dialog_completion_handlers(qapp):
    cfg = ConfigManager()
    dialog = DownloaderDialog(cfg)

    # Success completion calls accept
    with patch.object(dialog, "accept") as mock_accept:
        dialog.on_download_complete(True, "All models downloaded successfully.")
        mock_accept.assert_called_once()

    # Failure completion calls handle_error
    dialog.on_download_complete(False, "Connection failed.")
    assert "Error: Connection failed." in dialog.status_label.text()
    dialog.close()


@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.stat")
def test_download_worker_run_already_existing(mock_stat, mock_exists, qapp):
    mock_stat.return_value.st_size = 5000
    cfg = ConfigManager()
    worker = DownloadWorker(cfg)

    progress_updates = []
    worker.progress.connect(lambda pct, msg: progress_updates.append((pct, msg)))

    finished_called = False
    def on_finished():
        nonlocal finished_called
        finished_called = True
    worker.finished.connect(on_finished)

    download_finished_res = []
    worker.download_finished.connect(lambda s, m: download_finished_res.append((s, m)))

    worker.run()

    assert finished_called is True
    assert len(download_finished_res) == 1
    assert download_finished_res[0][0] is True
    assert any(pct == 100 for pct, _ in progress_updates)


@patch("requests.get")
@patch("pathlib.Path.exists", return_value=False)
@patch("builtins.open")
def test_download_worker_run_download(mock_open, mock_exists, mock_requests_get, qapp):
    mock_resp = MagicMock()
    mock_resp.headers = {"content-length": "1000"}
    mock_resp.iter_content.return_value = [b"chunk1" * 10, b"chunk2" * 10]
    mock_requests_get.return_value = mock_resp

    cfg = ConfigManager()
    worker = DownloadWorker(cfg)

    progress_updates = []
    worker.progress_updated.connect(lambda pct, msg: progress_updates.append((pct, msg)))

    finished_called = False
    def on_finished():
        nonlocal finished_called
        finished_called = True
    worker.finished.connect(on_finished)

    download_finished_res = []
    worker.download_finished.connect(lambda s, m: download_finished_res.append((s, m)))

    worker.run()

    assert mock_requests_get.called
    assert finished_called is True
    assert download_finished_res[0][0] is True
    assert any(pct == 100 for pct, _ in progress_updates)


@patch("requests.get", side_effect=requests.exceptions.Timeout("Connection timed out"))
@patch("pathlib.Path.exists", return_value=False)
def test_download_worker_timeout_handling(mock_exists, mock_requests_get, qapp):
    cfg = ConfigManager()
    worker = DownloadWorker(cfg)

    errors = []
    worker.error.connect(lambda err: errors.append(err))

    download_finished_res = []
    worker.download_finished.connect(lambda s, m: download_finished_res.append((s, m)))

    worker.run()

    assert len(errors) == 1
    assert "timeout" in errors[0].lower()
    assert len(download_finished_res) == 1
    assert download_finished_res[0][0] is False
