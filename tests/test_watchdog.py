import pytest
import time
import threading
from unittest.mock import patch

from src.core.watchdog import ThreadWatchdog

def test_watchdog_registration():
    wd = ThreadWatchdog(timeout_sec=0.5)
    # Start the watchdog but we'll stop it right away
    wd.start()
    
    tid = threading.get_ident()
    wd.register_task(tid)
    assert tid in wd.active_tasks
    
    wd.unregister_task(tid)
    assert tid not in wd.active_tasks
    wd.stop()

def test_watchdog_timeout():
    wd = ThreadWatchdog(timeout_sec=0.1)
    called = []
    wd.on_deadlock = lambda: called.append(True)
    
    wd.register_task(123)
    
    def side_effect(*args):
        wd.is_running = False
        
    real_time = time.time()
    with patch('src.core.watchdog.time.sleep', side_effect=side_effect):
        with patch('src.core.watchdog.time.time', return_value=real_time + 10.0):
            wd.is_running = True
            wd._monitor_loop()
            
    assert len(called) == 1
    assert 123 not in wd.active_tasks

def test_watchdog_wrap_thread():
    wd = ThreadWatchdog(timeout_sec=0.1)
    
    target_called = []
    def target():
        target_called.append(True)
        
    t = wd.wrap_thread(target)
    t.join(timeout=1.0)
    
    assert len(target_called) == 1
    # After completion, thread should be unregistered
    assert len(wd.active_tasks) == 0
