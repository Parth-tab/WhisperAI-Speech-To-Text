from src.injection.window_detect import WindowDetector


def test_window_detector():
    detector = WindowDetector()
    title, process, pid = detector.get_active_window_info()

    assert isinstance(title, str)
    assert isinstance(process, str)
    assert isinstance(pid, int)

    context, style, pid2 = detector.get_context()
    assert isinstance(context, str) and len(context) > 0
    assert isinstance(style, str)
