import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt, QThread, Signal
from src.utils.paths import get_asset_path

class DownloadWorker(QThread):
    progress = Signal(int, str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        
    def run(self):
        try:
            self._patch_tqdm()
            
            # 1. Download LLM
            self.progress.emit(0, "Downloading LLM (Qwen 1.5B)...")
            from src.llm.engine import _ensure_model, _MODELS_DIR, _MODEL_FILENAME
            _ensure_model(_MODELS_DIR, _MODEL_FILENAME)
            
            # 2. Download ASR (Whisper)
            self.progress.emit(0, "Downloading ASR Model...")
            from src.asr.engine import ASREngine
            model_selection = self.config_manager.get("model_selection", "base")
            if model_selection in ["tiny", "base", "small", "medium"]:
                model_size = f"{model_selection}.en"
            else:
                model_size = model_selection
                
            # By instantiating ASREngine, it will trigger the faster-whisper download
            # We don't need to keep the instance, we just want the download to happen
            ASREngine(model_size=model_size)
            
            self.progress.emit(100, "Download Complete!")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self._unpatch_tqdm()

    def _patch_tqdm(self):
        import tqdm
        self._original_tqdm = tqdm.tqdm
        self._original_auto_tqdm = tqdm.auto.tqdm
        
        worker_self = self
        
        class CustomTqdm(self._original_tqdm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                
            def update(self, n=1):
                super().update(n)
                if self.total and self.total > 0:
                    percent = int((self.n / self.total) * 100)
                    # Don't emit 100% until truly finished to avoid premature closing if there are multiple files
                    if percent > 99:
                        percent = 99
                    
                    desc = self.desc or "Downloading..."
                    # clean up huggingface desc
                    desc = desc.replace("Downloading", "").strip()
                    if desc:
                        msg = f"Downloading: {desc}"
                    else:
                        msg = "Downloading models..."
                        
                    worker_self.progress.emit(percent, msg)
                    
            def close(self):
                super().close()
                
        tqdm.tqdm = CustomTqdm
        tqdm.auto.tqdm = CustomTqdm

    def _unpatch_tqdm(self):
        import tqdm
        if hasattr(self, '_original_tqdm'):
            tqdm.tqdm = self._original_tqdm
            tqdm.auto.tqdm = self._original_auto_tqdm


class DownloaderDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WhisperAI - Initializing")
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        layout = QVBoxLayout(self)
        
        self.info_label = QLabel("Downloading required AI models for first run.\nThis may take a few minutes depending on your internet connection.")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        self.status_label = QLabel("Starting download...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.worker = DownloadWorker(config_manager)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.accept)
        self.worker.error.connect(self.handle_error)
        
    def start_download(self):
        self.worker.start()
        
    def update_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        
    def handle_error(self, err_msg):
        self.status_label.setText(f"Error: {err_msg}")
        self.status_label.setStyleSheet("color: red;")
        # Allow user to close on error
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        self.show() # Refresh flags
