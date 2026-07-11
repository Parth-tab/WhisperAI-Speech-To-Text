import sys
import threading
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal

from src.asr.engine import ASREngine
from src.llm.engine import LLMEngine
from src.core.pipeline import AIPipeline

from src.audio.capture import AudioCaptureEngine
from src.hotkey.listener import HotkeyListener, make_listener_from_config
from src.injection.window_detect import WindowDetector
from src.injection.injector import ClipboardInjector
from src.config.manager import ConfigManager
from src.gui.tray import SystemTrayApp
from src.gui.overlay import RecordingOverlay


class AppSignals(QObject):
    recording_started = Signal()
    recording_stopped = Signal()
    models_ready = Signal()
    status_update = Signal(str)


class WhisperAIApp:
    def __init__(self):
        self.config_manager = ConfigManager()
        self._models_loaded = False

        # Lightweight components — initialise immediately
        hotkey_str = self.config_manager.get("hotkey", "<ctrl>+<alt>+w")
        print(f"[App] Hotkey configured as: {hotkey_str}")
        self.hotkey_listener = make_listener_from_config(hotkey_str)
        self.window_detector = WindowDetector()
        self.injector = ClipboardInjector()

        # Heavy AI models — loaded lazily on a background thread
        self.audio_engine = None
        self.asr_engine = None
        self.llm_engine = None
        self.pipeline = None

        # Qt setup
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.signals = AppSignals()

        # Overlay
        self.overlay = RecordingOverlay()
        self.signals.recording_started.connect(self.overlay.show_overlay)
        self.signals.recording_stopped.connect(self.overlay.hide_overlay)

        # Tray — visible immediately so user knows app is running
        self.tray = SystemTrayApp(self.qt_app, self.config_manager, self.stop, settings_callback=self.on_settings_saved)
        self.tray.show()

        # Wire hotkey AFTER tray is visible
        self.hotkey_listener.set_callbacks(
            on_press=self.on_hotkey_press,
            on_release=self.on_hotkey_release,
        )

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
            print(f"[App] Hotkey updated to: {new_hotkey}")

        new_vad = new_settings.get("vad_threshold")
        if new_vad is not None and self.audio_engine and self.audio_engine.vad_engine:
            self.audio_engine.vad_engine.threshold = new_vad
            print(f"[App] VAD threshold updated to: {new_vad}")
            
        print("[App] Settings saved!")

    def start(self):
        self.hotkey_listener.start()

        # Load heavy models in a background thread so the tray appears instantly
        threading.Thread(target=self._load_models, daemon=True).start()

        # Block the main thread running the Qt event loop
        sys.exit(self.qt_app.exec())

    def _load_models(self):
        """Load ASR + LLM models on a background thread."""
        try:
            print("[App] Initializing Audio Engine (VAD)...")
            self.audio_engine = AudioCaptureEngine()
            self.audio_engine.on_recording_stopped = self._on_recording_stopped

            print("[App] Loading ASR model...")
            self.asr_engine = ASREngine()

            print("[App] Loading LLM model...")
            self.llm_engine = LLMEngine()

            self.pipeline = AIPipeline(self.asr_engine, self.llm_engine)

            self._models_loaded = True
            print("[App] All models loaded. Ready to dictate!")
            self.signals.models_ready.emit()
        except Exception as e:
            print(f"[App] ERROR loading models: {e}")

    def stop(self):
        self.hotkey_listener.stop()
        if self.audio_engine:
            self.audio_engine.stop_recording()

    def on_hotkey_press(self):
        if not self._models_loaded or not self.audio_engine:
            print("[App] Models still loading, please wait...")
            return
        print("[App] HOTKEY PRESSED! Starting recording...")
        self.audio_engine.start_recording()
        self.signals.recording_started.emit()

    def on_hotkey_release(self):
        if not self._models_loaded or not self.audio_engine:
            return
        print("[App] HOTKEY RELEASED! Stopping recording...")
        self.audio_engine.stop_recording()

    def _on_recording_stopped(self, audio_data):
        self.signals.recording_stopped.emit()
        print(f"[App] AUDIO CAPTURED: {len(audio_data)} frames")
        if len(audio_data) == 0 or not self._models_loaded or self.pipeline is None:
            print("[App] Empty audio or models not loaded. Aborting pipeline.")
            return
        context = self.window_detector.get_context()
        print(f"[App] Active window context: {context}")
        threading.Thread(
            target=self._run_pipeline_and_inject,
            args=(audio_data, context),
            daemon=True,
        ).start()

    def _run_pipeline_and_inject(self, audio_data, context):
        try:
            final_text = self.pipeline.process_audio(audio_data, context)
            if final_text:
                self.injector.inject_text(final_text)
        except Exception as e:
            print(f"[App] Error in pipeline: {e}")
