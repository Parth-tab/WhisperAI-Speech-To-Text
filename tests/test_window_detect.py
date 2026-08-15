from src.injection.window_detect import WindowDetector


def test_window_detector():
    detector = WindowDetector()
    title, process, pid = detector.get_active_window_info()

    assert isinstance(title, str)
    assert isinstance(process, str)
    assert isinstance(pid, int)

    context, style, _ = detector.get_context()
    assert isinstance(context, str) and len(context) > 0
    assert isinstance(style, str)


def test_sanitize_window_title():
    from src.injection.window_detect import _sanitize_window_title

    t1 = "WhisperAI - speech-to-text / AI model is y does your graphics card have?"
    res1 = _sanitize_window_title(t1)
    assert res1 == "WhisperAI speech to text AI"
    assert len(res1) <= 30
    assert "graphics" not in res1
