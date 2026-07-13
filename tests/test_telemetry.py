import pytest
from unittest.mock import patch, MagicMock
from src.core.telemetry import TelemetryTracker

def test_telemetry_logging():
    tracker = TelemetryTracker()
    
    tracker.log_transcription_latency(1.5)
    assert len(tracker.metrics["transcription_latency"]) == 1
    assert tracker.metrics["transcription_latency"][0] == 1.5
    
    tracker.log_token_generation_speed(45.2)
    assert len(tracker.metrics["token_generation_speed"]) == 1
    assert tracker.metrics["token_generation_speed"][0] == 45.2

@patch('src.core.telemetry.psutil.Process')
def test_get_current_memory_mb(mock_process):
    mock_proc_instance = MagicMock()
    mock_memory_info = MagicMock()
    mock_memory_info.rss = 10485760 # 10 MB
    mock_proc_instance.memory_info.return_value = mock_memory_info
    mock_process.return_value = mock_proc_instance
    
    tracker = TelemetryTracker()
    mem_mb = tracker.get_current_memory_mb()
    assert mem_mb == 10.0

def test_telemetry_background_loop():
    tracker = TelemetryTracker()
    
    # Run the loop once by setting is_running to False inside time.sleep
    def side_effect(*args):
        tracker.is_running = False
        
    with patch('src.core.telemetry.time.sleep', side_effect=side_effect):
        tracker.is_running = True
        tracker._log_loop(interval=0.1)
        
    assert len(tracker.metrics["memory_usage_mb"]) == 1
