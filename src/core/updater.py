import sys
import os
import subprocess
import urllib.request
import json
from pathlib import Path
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from src.core.version import __version__

class UpdateCheckWorker(QThread):
    update_available = Signal(str, str) # version, download_url
    error = Signal(str)

    def run(self):
        try:
            url = "https://api.github.com/repos/Parth/WhisperAI-Speech-To-Text/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'WhisperAI-Updater'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                latest_version = data.get("tag_name", "")
                if latest_version and latest_version > __version__:
                    # Find the setup.exe asset
                    download_url = None
                    for asset in data.get("assets", []):
                        if asset.get("name", "").endswith(".exe") and "Setup" in asset.get("name", ""):
                            download_url = asset.get("browser_download_url")
                            break
                            
                    if not download_url:
                        # Fallback to the first exe if Setup is not in the name
                        for asset in data.get("assets", []):
                            if asset.get("name", "").endswith(".exe"):
                                download_url = asset.get("browser_download_url")
                                break
                                
                    if download_url:
                        self.update_available.emit(latest_version, download_url)
        except Exception as e:
            self.error.emit(str(e))


class UpdateDownloadWorker(QThread):
    progress = Signal(int)
    finished = Signal(str) # file path
    error = Signal(str)

    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url

    def run(self):
        try:
            temp_dir = Path(os.environ.get("TEMP", os.path.expanduser("~")))
            installer_path = temp_dir / "WhisperAISetup_Update.exe"
            
            def report(blocknum, blocksize, totalsize):
                if totalsize > 0:
                    percent = int(blocknum * blocksize * 100 / totalsize)
                    if percent > 100:
                        percent = 100
                    self.progress.emit(percent)
                    
            urllib.request.urlretrieve(self.download_url, str(installer_path), reporthook=report)
            self.finished.emit(str(installer_path))
        except Exception as e:
            self.error.emit(str(e))


class AutoUpdater:
    def __init__(self, tray_icon=None):
        self.tray_icon = tray_icon
        self.check_worker = UpdateCheckWorker()
        self.check_worker.update_available.connect(self.on_update_available)
        self.download_worker = None
        self.progress_dialog = None
        self._pending_download_url = None

    def start_check(self):
        self.check_worker.start()

    def on_update_available(self, version, download_url):
        self._pending_download_url = download_url
        if self.tray_icon:
            # We connect to messageClicked to trigger the download
            # Make sure we only connect once by disconnecting any previous connections if needed
            try:
                self.tray_icon.messageClicked.disconnect()
            except Exception:
                pass
            
            self.tray_icon.messageClicked.connect(self._start_pending_download)
            self.tray_icon.showMessage(
                "Update Available", 
                f"Version {version} is ready. Click here to download and install.", 
                self.tray_icon.MessageIcon.Information, 
                10000
            )

    def _start_pending_download(self):
        if self._pending_download_url:
            self.start_download(self._pending_download_url)
            self._pending_download_url = None

    def start_download(self, download_url):
        self.progress_dialog = QProgressDialog("Downloading update...", "Cancel", 0, 100)
        self.progress_dialog.setWindowTitle("WhisperAI Updater")
        self.progress_dialog.setWindowFlags(self.progress_dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        self.progress_dialog.setWindowModality(Qt.NonModal) # IMPORTANT: Non-modal
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setValue(0)
        
        self.download_worker = UpdateDownloadWorker(download_url)
        self.download_worker.progress.connect(self.progress_dialog.setValue)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        
        self.progress_dialog.canceled.connect(self.download_worker.terminate)
        
        self.download_worker.start()
        self.progress_dialog.show()

    def on_download_finished(self, installer_path):
        if self.progress_dialog:
            self.progress_dialog.close()
            
        try:
            subprocess.Popen([installer_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/FORCECLOSEAPPLICATIONS"])
        except Exception as e:
            if self.tray_icon:
                self.tray_icon.showMessage("Update Error", f"Failed to launch installer: {e}", self.tray_icon.MessageIcon.Critical, 5000)
            return
            
        sys.exit(0)
        
    def on_download_error(self, err_msg):
        if self.progress_dialog:
            self.progress_dialog.close()
        if self.tray_icon:
            self.tray_icon.showMessage("Update Error", f"Download failed: {err_msg}", self.tray_icon.MessageIcon.Critical, 5000)
