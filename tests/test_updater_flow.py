import json
import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.core.updater import AutoUpdater, UpdateCheckWorker, UpdateDownloadWorker


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


@patch("src.core.updater.urllib.request.urlopen")
def test_update_check_worker_available(mock_urlopen, qapp):
    fake_release = {
        "tag_name": "v99.0.0",
        "assets": [
            {
                "name": "WhisperAISetup_v99.0.0.exe",
                "browser_download_url": "https://github.com/Parth/WhisperAI/releases/download/v99.0.0/setup.exe"
            }
        ]
    }
    
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_release).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    worker = UpdateCheckWorker()
    available_updates = []
    worker.update_available.connect(lambda v, url: available_updates.append((v, url)))

    worker.run()
    assert len(available_updates) == 1
    assert available_updates[0][0] == "v99.0.0"
    assert "setup.exe" in available_updates[0][1]


@patch("src.core.updater.urllib.request.urlretrieve")
def test_update_download_worker_run(mock_retrieve, tmp_path, qapp):
    mock_retrieve.side_effect = lambda url, path, reporthook: (
        reporthook(1, 1024, 1024),
        None
    )

    worker = UpdateDownloadWorker("https://fake.url/setup.exe")
    progress_vals = []
    worker.progress.connect(lambda p: progress_vals.append(p))
    
    finished_paths = []
    worker.finished.connect(lambda p: finished_paths.append(p))

    worker.run()
    assert len(finished_paths) == 1
    assert "WhisperAISetup_Update.exe" in finished_paths[0]
    assert 100 in progress_vals


def test_auto_updater_tray_notification(qapp):
    mock_tray = MagicMock()
    updater = AutoUpdater(tray_icon=mock_tray)
    
    updater.on_update_available("v2.0.0", "https://download.url/setup.exe")
    assert updater._pending_download_url == "https://download.url/setup.exe"
    mock_tray.showMessage.assert_called_once()
