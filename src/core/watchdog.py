import time
import threading
import logging
from typing import Callable, Dict

logger = logging.getLogger("Watchdog")


class ThreadWatchdog:
    def __init__(self, timeout_sec: float = 60.0):
        self.timeout_sec = timeout_sec
        self.active_tasks: Dict[int, float] = {}
        self.lock = threading.Lock()
        self.is_running = False
        self._bg_thread = None
        self.on_deadlock: Callable[[], None] = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._bg_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._bg_thread.start()
        logger.info("Watchdog started.")

    def stop(self):
        self.is_running = False
        if self._bg_thread:
            self._bg_thread.join(timeout=2.0)
        logger.info("Watchdog stopped.")

    def register_task(self, thread_id: int):
        with self.lock:
            self.active_tasks[thread_id] = time.time()

    def unregister_task(self, thread_id: int):
        with self.lock:
            self.active_tasks.pop(thread_id, None)

    def _monitor_loop(self):
        while self.is_running:
            now = time.time()
            deadlocked = False
            with self.lock:
                for tid, start_time in list(self.active_tasks.items()):
                    if now - start_time > self.timeout_sec:
                        logger.error(
                            f"Watchdog: Thread {tid} deadlocked (>{self.timeout_sec}s)."
                        )
                        deadlocked = True
                        del self.active_tasks[tid]

            if deadlocked and self.on_deadlock:
                logger.warning("Watchdog: Triggering recovery...")
                try:
                    self.on_deadlock()
                except Exception as e:
                    logger.error(f"Watchdog recovery failed: {e}")

            time.sleep(5.0)

    def wrap_thread(self, target, args=(), kwargs={}):
        def wrapped_target():
            tid = threading.get_ident()
            self.register_task(tid)
            try:
                target(*args, **kwargs)
            finally:
                self.unregister_task(tid)

        t = threading.Thread(target=wrapped_target, daemon=True)
        t.start()
        return t


# Global singleton
watchdog = ThreadWatchdog(timeout_sec=30.0)
