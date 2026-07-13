from src.injection.window_detect import WindowDetector

def test_window_detector():
    detector = WindowDetector()
    title, process = detector.get_active_window_info()
    
    assert isinstance(title, str)
    assert isinstance(process, str)
    
    context = detector.get_context()
    assert isinstance(context, str) and len(context) > 0
