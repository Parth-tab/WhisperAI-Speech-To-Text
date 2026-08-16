import logging
from pathlib import Path

import requests
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout

from src.config.manager import ConfigManager

logger = logging.getLogger("whisperai")


class DownloadWorker(QThread):
    progress = Signal(int, str)
    progress_updated = Signal(int, str)
    finished = Signal()
    error = Signal(str)
    download_finished = Signal(bool, str)

    def __init__(self, config_manager_or_dir=None):
        super().__init__()
        if isinstance(config_manager_or_dir, ConfigManager):
            self.config_manager = config_manager_or_dir
            self.models_dir = Path.home() / ".whisperai" / "models"
        elif isinstance(config_manager_or_dir, (str, Path)):
            self.models_dir = Path(config_manager_or_dir)
            self.config_manager = ConfigManager()
        else:
            self.config_manager = ConfigManager()
            self.models_dir = Path.home() / ".whisperai" / "models"

        self.is_running = True

    def _emit_progress(self, percent: int, msg: str):
        self.progress.emit(percent, msg)
        self.progress_updated.emit(percent, msg)

    def _download_file(
        self,
        url: str,
        target_path: Path,
        display_name: str,
        base_pct: int,
        pct_span: int,
    ):
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists() and target_path.stat().st_size > 1000:
            self._emit_progress(base_pct + pct_span, f"{display_name} already exists.")
            return

        tmp_path = target_path.with_suffix(".tmp")
        try:
            self._emit_progress(base_pct, f"Downloading {display_name}...")
            response = requests.get(url, stream=True, timeout=(10, 30))
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            chunk_size = 128 * 1024  # 128KB chunks

            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not self.is_running:
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            file_pct = downloaded_size / total_size
                            current_total_pct = int(base_pct + (file_pct * pct_span))
                            current_total_pct = min(
                                current_total_pct, base_pct + pct_span - 1
                            )
                            self._emit_progress(
                                current_total_pct,
                                f"Downloading {display_name}: {int(file_pct * 100)}%",
                            )

            if tmp_path.exists():
                tmp_path.rename(target_path)
            self._emit_progress(base_pct + pct_span, f"Downloaded {display_name}")
        except Exception as e:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            raise e

    def run(self):
        self.is_running = True
        try:
            # 1. Silero VAD Model (~1.5 MB) -> 0% to 5%
            vad_path = self.models_dir / "vad" / "silero_vad.onnx"
            vad_legacy = self.models_dir / "silero_vad.onnx"
            if not vad_path.exists() and not vad_legacy.exists():
                self._download_file(
                    url="https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx",
                    target_path=vad_path,
                    display_name="Silero VAD",
                    base_pct=0,
                    pct_span=5,
                )
            else:
                self._emit_progress(5, "Silero VAD already exists.")

            # 2. LLM Model (Qwen2.5-1.5B GGUF ~1.1 GB) -> 5% to 55%
            llm_path = self.models_dir / "llm" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
            self._download_file(
                url="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
                target_path=llm_path,
                display_name="LLM (Qwen 1.5B)",
                base_pct=5,
                pct_span=50,
            )

            # 3. Whisper ASR Model -> 55% to 100%
            model_selection = self.config_manager.get(
                "model_selection", "distil-large-v3"
            )
            lang_setting = self.config_manager.get("language", "auto")
            if (
                model_selection in ["tiny", "base", "small", "medium"]
                and lang_setting == "en"
            ):
                model_size = f"{model_selection}.en"
            else:
                model_size = model_selection

            if model_size == "large-v3-turbo":
                repo_id = "Systran/faster-whisper-large-v3-turbo"
            elif model_size in ("distil-large-v3", "faster-distil-whisper-large-v3"):
                repo_id = "Systran/faster-distil-whisper-large-v3"
            elif "/" in model_size:
                repo_id = model_size
            else:
                repo_id = f"Systran/faster-whisper-{model_size}"

            asr_dir = self.models_dir / "whisper" / model_size

            # Small metadata files (55% to 60%)
            meta_files = [
                "config.json",
                "preprocessor_config.json",
                "tokenizer.json",
                "vocabulary.json",
            ]
            for i, fname in enumerate(meta_files):
                sub_span = max(1, 5 // len(meta_files))
                self._download_file(
                    url=f"https://huggingface.co/{repo_id}/resolve/main/{fname}",
                    target_path=asr_dir / fname,
                    display_name=f"ASR ({fname})",
                    base_pct=55 + (i * sub_span),
                    pct_span=sub_span,
                )

            # Main model weights (60% to 100%)
            self._download_file(
                url=f"https://huggingface.co/{repo_id}/resolve/main/model.bin",
                target_path=asr_dir / "model.bin",
                display_name=f"ASR weights ({model_size})",
                base_pct=60,
                pct_span=40,
            )

            self._emit_progress(100, "Download Complete!")
            self.finished.emit()
            self.download_finished.emit(True, "All models downloaded successfully.")

        except requests.exceptions.Timeout:
            err_msg = "Network timeout. Please check your connection and restart."
            logger.error(f"[Downloader] {err_msg}")
            self.error.emit(err_msg)
            self.download_finished.emit(False, err_msg)
        except Exception as e:
            err_msg = f"Download failed: {str(e)}"
            logger.error(f"[Downloader] {err_msg}")
            self.error.emit(err_msg)
            self.download_finished.emit(False, err_msg)

    def stop(self):
        self.is_running = False


class DownloaderDialog(QDialog):
    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WhisperAI - Initializing")
        self.setMinimumSize(420, 170)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowCloseButtonHint
        )

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

        self.info_label = QLabel(
            "Downloading required AI models for first run.\nThis may take a few minutes depending on your internet connection."
        )
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
        self.worker.download_finished.connect(self.on_download_complete)

    def start_download(self):
        if not self.worker.isRunning():
            self.worker.start()

    def showEvent(self, event):
        super().showEvent(event)
        self.start_download()

    def update_progress(self, percent: int, message: str):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def on_download_complete(self, success: bool, message: str):
        if success:
            self.accept()
        else:
            self.handle_error(message)

    def handle_error(self, err_msg: str):
        self.status_label.setText(f"Error: {err_msg}")
        self.status_label.setStyleSheet("color: #EF4444; font-weight: bold;")
