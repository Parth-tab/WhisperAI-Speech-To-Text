from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout


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

            # 1. Download Silero VAD
            self.progress.emit(0, "Downloading VAD Model...")
            from pathlib import Path
            import urllib.request
            vad_dir = Path.home() / ".whisperai" / "models" / "vad"
            vad_dir.mkdir(parents=True, exist_ok=True)
            vad_path = vad_dir / "silero_vad.onnx"
            vad_legacy_path = Path.home() / ".whisperai" / "models" / "silero_vad.onnx"

            if not vad_path.exists() and not vad_legacy_path.exists():
                url = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
                tmp_path = vad_path.with_suffix(".tmp")
                try:
                    urllib.request.urlretrieve(url, tmp_path)
                    if tmp_path.stat().st_size > 100000:
                        tmp_path.rename(vad_path)
                    else:
                        raise Exception("Downloaded VAD model file is too small.")
                except Exception as e:
                    if tmp_path.exists():
                        tmp_path.unlink()
                    raise e

            # 2. Download LLM
            self.progress.emit(25, "Downloading LLM (Qwen 1.5B)...")
            from src.llm.engine import _MODEL_FILENAME, _MODELS_DIR, _ensure_model
            _ensure_model(_MODELS_DIR, _MODEL_FILENAME)

            # 3. Download ASR (Whisper)
            self.progress.emit(60, "Downloading ASR Model...")
            from src.asr.engine import ASREngine
            model_selection = self.config_manager.get("model_selection", "base")
            lang_setting = self.config_manager.get("language", "auto")
            if model_selection in ["tiny", "base", "small", "medium"] and lang_setting == "en":
                model_size = f"{model_selection}.en"
            else:
                model_size = model_selection

            # By instantiating ASREngine, it will trigger the faster-whisper download
            # We don't need to keep the instance, we just want the download to happen
            ASREngine(model_size=model_size, language=lang_setting)

            self.progress.emit(100, "Download Complete!")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self._unpatch_tqdm()

    def _patch_tqdm(self):
        import tqdm
        import tqdm.auto
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
                    percent = min(percent, 99)

                    desc = self.desc or "Downloading..."
                    # clean up huggingface desc
                    msg = f"Downloading: {desc}" if desc else "Downloading models..."
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
        self.setMinimumSize(420, 170)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        from src.utils.theme_compiler import compile_qss
        qss_template = """
            QDialog {
                background-color: {{bg_primary}};
                color: {{text_primary}};
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: {{text_primary}};
            }
            QProgressBar {
                border: 1px solid {{border_subtle}};
                border-radius: 4px;
                text-align: center;
                background-color: {{bg_secondary}};
                color: {{text_primary}};
            }
            QProgressBar::chunk {
                background-color: {{accent_idle}};
                border-radius: 3px;
            }
        """
        self.setStyleSheet(compile_qss(qss_template, "dark"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

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
        if not self.worker.isRunning():
            self.worker.start()

    def showEvent(self, event):
        super().showEvent(event)
        self.start_download()

    def update_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def handle_error(self, err_msg):
        self.status_label.setText(f"Error: {err_msg}")
        self.status_label.setStyleSheet("color: #EF4444; font-weight: bold;")
