import time
import psutil
import logging
import threading
from typing import Dict, List


def setup_telemetry_logger():
    logger = logging.getLogger("Telemetry")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


telemetry_logger = setup_telemetry_logger()


class TelemetryTracker:
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            "transcription_latency": [],
            "token_generation_speed": [],
            "memory_usage_mb": [],
        }
        self.lock = threading.Lock()
        self.is_running = False
        self._bg_thread = None

    def start_background_logging(self, interval: float = 5.0):
        if self.is_running:
            return
        self.is_running = True
        self._bg_thread = threading.Thread(
            target=self._log_loop, args=(interval,), daemon=True
        )
        self._bg_thread.start()
        telemetry_logger.info("Telemetry background logging started.")

    def stop_background_logging(self):
        self.is_running = False
        if self._bg_thread:
            self._bg_thread.join(timeout=2.0)
        telemetry_logger.info("Telemetry background logging stopped.")

    def _log_loop(self, interval: float):
        while self.is_running:
            mem_mb = self.get_current_memory_mb()
            with self.lock:
                self.metrics["memory_usage_mb"].append(mem_mb)

            telemetry_logger.info(f"Current Memory Usage: {mem_mb:.2f} MB")
            time.sleep(interval)

    def get_current_memory_mb(self) -> float:
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def log_transcription_latency(self, latency_sec: float):
        with self.lock:
            self.metrics["transcription_latency"].append(latency_sec)
        telemetry_logger.info(f"Transcription Latency: {latency_sec:.3f} s")

    def log_token_generation_speed(self, tokens_per_sec: float):
        with self.lock:
            self.metrics["token_generation_speed"].append(tokens_per_sec)
        telemetry_logger.info(f"Token Generation Speed: {tokens_per_sec:.2f} tokens/s")


# Global singleton
telemetry = TelemetryTracker()
