import numpy as np
import sounddevice as sd
import logging
from collections import deque
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger("whisperai")


class WakeWordWorker(QThread):
    wake_word_detected = Signal(object)  # Emits np.ndarray (1s pre-roll audio)

    def __init__(self, sample_rate: int = 16000, energy_threshold: float = 0.08):
        super().__init__()
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.running = False
        # 1-second circular pre-roll buffer
        self.buffer = deque(maxlen=sample_rate)

    def run(self):
        self.running = True
        logger.info("[WakeWordWorker] Background wake-word listener started.")

        def callback(indata, frames, time_info, status):
            if status or not self.running:
                return
            mono = indata[:, 0] if indata.ndim > 1 else indata.flatten()
            self.buffer.extend(mono.tolist())

            if self._detect_wake_word(mono):
                pre_roll_audio = np.array(self.buffer, dtype=np.float32)
                logger.info("[WakeWordWorker] Wake word pattern detected. Emitting pre-roll audio.")
                self.wake_word_detected.emit(pre_roll_audio)

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=callback,
                blocksize=1600,
            ):
                while self.running:
                    QThread.msleep(100)
        except Exception as e:
            logger.warning(f"[WakeWordWorker] InputStream failed: {e}")
        finally:
            logger.info("[WakeWordWorker] Background wake-word listener stopped.")

    def _detect_wake_word(self, audio_chunk: np.ndarray) -> bool:
        """
        Lightweight acoustic / energy burst keyword spotting heuristic.
        """
        if len(audio_chunk) == 0:
            return False
        rms = np.sqrt(np.mean(audio_chunk**2))
        return bool(rms > self.energy_threshold)

    def stop(self):
        self.running = False
