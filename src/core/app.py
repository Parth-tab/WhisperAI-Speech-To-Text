import sys
import threading
import queue
import platform
import psutil
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QIcon
from src.utils.paths import get_asset_path

from src.asr.engine import ASREngine
from src.llm.engine import LLMEngine
from src.core.pipeline import AIPipeline

from src.audio.capture import AudioWorker
from src.hotkey.listener import make_listener_from_config
from src.injection.window_detect import WindowDetector
from src.injection.injector import ClipboardInjector
from src.config.manager import ConfigManager
from src.gui.tray import SystemTrayApp
from src.gui.overlay import RecordingOverlay
from src.gui.flow_bubble import FlowBubble, BubbleState


class AppSignals(QObject):
    recording_started = Signal()
    recording_stopped = Signal()
    models_ready = Signal()
    status_update = Signal(str)
    audio_level = Signal(float)
    bubble_state = Signal(object)
    hotkey_pressed = Signal()
    hotkey_released = Signal()
    audio_capture_finished = Signal(object)


class WhisperAIApp:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.state_lock = threading.RLock()
        self._models_loaded = False
        self.transcription_queue = queue.Queue()

        # Lightweight components — initialise immediately
        hotkey_str = self.config_manager.get("hotkey", "<ctrl>+<alt>+w")
        pass
        self.hotkey_listener = make_listener_from_config(hotkey_str)
        self.window_detector = WindowDetector(self.config_manager)
        self.injector = ClipboardInjector()

        # Heavy AI models — loaded lazily on a background thread
        self.audio_worker = None
        self.asr_engine = None
        self.llm_engine = None
        self.pipeline = None

        # Qt setup
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)
        self.qt_app.setWindowIcon(QIcon(get_asset_path("src/assets/branding/logo.ico")))

        self.signals = AppSignals()

        # Overlay
        self.overlay = RecordingOverlay()
        self.signals.recording_started.connect(self.overlay.show_overlay)
        self.signals.recording_stopped.connect(self.overlay.hide_overlay)
        self.signals.audio_level.connect(self.overlay.update_level)

        # Flow Bubble
        self.bubble = FlowBubble(self.config_manager)
        self.bubble.clicked.connect(self.toggle_recording)
        self.signals.audio_level.connect(self.bubble.update_audio_level)
        self.signals.bubble_state.connect(self.bubble.set_state)
        self.signals.hotkey_pressed.connect(self.handle_hotkey_press)
        self.signals.hotkey_released.connect(self.handle_hotkey_release)
        self.bubble.show()

        # Tray — visible immediately so user knows app is running
        self.tray = SystemTrayApp(
            self.qt_app,
            self.config_manager,
            self.stop,
            settings_callback=self.on_settings_saved,
        )
        self.tray.show()

        # Wire hotkey AFTER tray is visible
        self.hotkey_listener.set_callbacks(
            on_press=self.on_hotkey_press,
            on_release=self.on_hotkey_release,
        )

        from src.core.telemetry import telemetry
        from src.core.watchdog import watchdog

        self.telemetry = telemetry
        self.watchdog = watchdog
        self.watchdog.on_deadlock = self._on_deadlock

    def on_settings_saved(self, new_settings: dict):
        new_hotkey = new_settings.get("hotkey")
        if new_hotkey:
            self.hotkey_listener.stop()
            self.hotkey_listener = make_listener_from_config(new_hotkey)
            self.hotkey_listener.set_callbacks(
                on_press=self.on_hotkey_press,
                on_release=self.on_hotkey_release,
            )
            self.hotkey_listener.start()
            pass

        is_whisper = new_settings.get(
            "whisper_mode", self.config_manager.get("whisper_mode", False)
        )
        base_vad = new_settings.get(
            "vad_threshold", self.config_manager.get("vad_threshold", 0.5)
        )
        if is_whisper:
            new_vad = self.config_manager.get("whisper_vad_threshold", 0.2)
        else:
            new_vad = base_vad

        with self.state_lock:
            if self.audio_worker and getattr(self.audio_worker, 'vad_engine', None):
                self.audio_worker.vad_engine.threshold = new_vad

    def _check_and_download_models(self):
        from pathlib import Path
        from src.llm.engine import _MODELS_DIR, _MODEL_FILENAME
        from src.asr.engine import _WHISPER_CACHE
        
        llm_path = Path(_MODELS_DIR) / _MODEL_FILENAME
        model_selection = self.config_manager.get("model_selection", "base")
        model_size = f"{model_selection}.en" if model_selection in ["tiny", "base", "small", "medium"] else model_selection
        
        needs_download = False
        if not llm_path.exists():
            needs_download = True
        else:
            whisper_dir = Path(_WHISPER_CACHE)
            if not whisper_dir.exists():
                needs_download = True
            else:
                found = False
                for item in whisper_dir.iterdir():
                    if item.is_dir() and model_size in item.name:
                        found = True
                        break
                if not found:
                    needs_download = True
                    
        if needs_download:
            from src.gui.downloader_dialog import DownloaderDialog
            dialog = DownloaderDialog(self.config_manager)
            dialog.start_download()
            dialog.exec()
            
    def start(self):
        self._pin_process_to_p_cores()
        self.hotkey_listener.start()
        self.telemetry.start_background_logging(interval=5.0)
        self.watchdog.start()
        threading.Thread(target=self._transcription_worker, daemon=True).start()

        # Check and download models with UI if missing
        self._check_and_download_models()

        # Start silent auto-update check in background
        from src.core.updater import AutoUpdater
        self.updater = AutoUpdater(tray_icon=self.tray)
        self.updater.start_check()

        # Load heavy models in a background thread so the tray appears instantly
        self.watchdog.wrap_thread(target=self._load_models)

        # Block the main thread running the Qt event loop
        sys.exit(self.qt_app.exec())

    def _pin_process_to_p_cores(self):
        """
        Heuristic to detect and pin the process to Performance Cores (P-cores) on Windows.
        On Intel hybrid CPUs, P-cores have Hyper-Threading (2 logical processors per physical core),
        while E-cores do not (1 logical processor per physical core).
        P = logical_cores - physical_cores
        """
        if platform.system() != "Windows":
            return

        try:
            logical_cores = psutil.cpu_count(logical=True)
            physical_cores = psutil.cpu_count(logical=False)

            if not logical_cores or not physical_cores:
                return

            # If symmetric (all HT or no HT), no need to pin
            if logical_cores == physical_cores or logical_cores == physical_cores * 2:
                return

            p_cores = logical_cores - physical_cores
            p_threads = 2 * p_cores

            # Intel typically schedules P-core logical processors first
            if p_threads < logical_cores and p_threads > 0:
                p_core_indices = list(range(p_threads))
                p = psutil.Process()
                p.cpu_affinity(p_core_indices)
                pass

        except Exception:
            pass

    def _load_models(self):
        """Load ASR + LLM models on a background thread in parallel."""
        try:
            pass
            
            model_selection = self.config_manager.get("model_selection", "base")
            if model_selection in ["tiny", "base", "small", "medium"]:
                model_size = f"{model_selection}.en"
            else:
                model_size = model_selection
                
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_asr = executor.submit(ASREngine, model_size)
                future_llm = executor.submit(LLMEngine)

            with self.state_lock:
                self.asr_engine = future_asr.result()
                self.llm_engine = future_llm.result()

                self.pipeline = AIPipeline(
                    self.asr_engine, self.llm_engine, self.config_manager
                )

                self._models_loaded = True

            pass
            self.signals.models_ready.emit()
        except Exception:
            pass

    def stop(self):
        self.hotkey_listener.stop()
        self.telemetry.stop_background_logging()
        self.watchdog.stop()
        self.transcription_queue.put(None)
        with self.state_lock:
            if self.audio_worker and self.audio_worker.isRunning():
                self.audio_worker.stop()

    def _on_audio_level_changed(self, level: float):
        self.signals.audio_level.emit(level)

    def _on_deadlock(self):
        pass
        self.signals.status_update.emit("Restarting (Deadlock)...")
        with self.state_lock:
            self._models_loaded = False
            if self.audio_worker and self.audio_worker.isRunning():
                self.audio_worker.stop()
        self.watchdog.wrap_thread(target=self._load_models)

    def toggle_recording(self):
        with self.state_lock:
            if not self._models_loaded:
                return

            if self.audio_worker and self.audio_worker.isRunning():
                self.audio_worker.stop()
            else:
                is_whisper = self.config_manager.get("whisper_mode", False)
                base_vad = self.config_manager.get("vad_threshold", 0.5)
                new_vad = self.config_manager.get("whisper_vad_threshold", 0.2) if is_whisper else base_vad
                
                self.audio_worker = AudioWorker(use_vad=True, vad_threshold=new_vad)
                self.audio_worker.connection_successful.connect(self._on_recording_started)
                self.audio_worker.recording_failed.connect(self._on_recording_failed)
                self.audio_worker.audio_chunk_ready.connect(self._on_audio_chunk)
                self.audio_worker.audio_level_changed.connect(self._on_audio_level_changed)
                self.audio_worker.recording_stopped.connect(self._on_recording_stopped)
                
                self.signals.bubble_state.emit(BubbleState.PROCESSING)
                self.audio_worker.start()

    def on_hotkey_press(self):
        self.signals.hotkey_pressed.emit()

    def handle_hotkey_press(self):
        with self.state_lock:
            if not self._models_loaded:
                return
            if not (self.audio_worker and self.audio_worker.isRunning()):
                is_whisper = self.config_manager.get("whisper_mode", False)
                base_vad = self.config_manager.get("vad_threshold", 0.5)
                new_vad = self.config_manager.get("whisper_vad_threshold", 0.2) if is_whisper else base_vad
                
                self.audio_worker = AudioWorker(use_vad=True, vad_threshold=new_vad)
                self.audio_worker.connection_successful.connect(self._on_recording_started)
                self.audio_worker.recording_failed.connect(self._on_recording_failed)
                self.audio_worker.audio_chunk_ready.connect(self._on_audio_chunk)
                self.audio_worker.audio_level_changed.connect(self._on_audio_level_changed)
                self.audio_worker.recording_stopped.connect(self._on_recording_stopped)
                
                self.signals.bubble_state.emit(BubbleState.PROCESSING)
                self.audio_worker.start()

    def on_hotkey_release(self):
        self.signals.hotkey_released.emit()

    def handle_hotkey_release(self):
        with self.state_lock:
            if self.audio_worker and self.audio_worker.isRunning():
                self.audio_worker.stop()



    @Slot()
    def _on_recording_started(self):
        self.signals.recording_started.emit()
        self.signals.bubble_state.emit(BubbleState.RECORDING)

    @Slot(str)
    def _on_recording_failed(self, err_msg):
        print(f"Recording failed: {err_msg}")
        self.signals.bubble_state.emit(BubbleState.IDLE)
        self.signals.recording_stopped.emit()
        with self.state_lock:
            if self.audio_worker:
                self.audio_worker.wait(1000) # Gracefully join thread
        if hasattr(self, 'tray'):
            self.tray.showMessage("Hardware Failure", f"Failed to open audio stream:\n\n{err_msg}")

    @Slot(object)
    def _on_audio_chunk(self, chunk):
        pass  # Intentionally disabled

    @Slot(float)
    def _on_audio_level_changed(self, level):
        self.signals.audio_level.emit(level)

    @Slot(object)
    def _on_recording_stopped(self, audio_data):
        self.signals.recording_stopped.emit()
        self.signals.bubble_state.emit(BubbleState.PROCESSING)

        with self.state_lock:
            if len(audio_data) == 0 or not self._models_loaded or self.pipeline is None:
                self.signals.bubble_state.emit(BubbleState.IDLE)
                return
            pipeline_ref = self.pipeline

        context_tuple = self.window_detector.get_context()
        pass
        self.transcription_queue.put((audio_data, context_tuple, pipeline_ref))

    def _transcription_worker(self):
        from src.data.stats_store import stats_store

        while True:
            task = self.transcription_queue.get()
            if task is None:
                break
            audio_data, context_tuple, pipeline_ref = task
            try:
                final_text = pipeline_ref.process_audio(
                    audio_data,
                    context=context_tuple[0],
                    profile_id=context_tuple[1],
                    pid=context_tuple[2],
                )
                if final_text:
                    self.injector.inject_text(final_text)
                    duration_sec = len(audio_data) / 16000.0
                    stats_store.log_session(duration_sec, final_text)
            except Exception:
                pass
            finally:
                self.signals.bubble_state.emit(BubbleState.IDLE)
