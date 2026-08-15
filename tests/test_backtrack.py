from src.utils.backtrack_detector import BacktrackDetector, backtrack_detector


def test_backtrack_markers():
    detector = BacktrackDetector()

    # "actually"
    res = detector.process("meet at four actually five")
    assert res == "<original>meet at four</original> <correction>actually five</correction>"

    # "i mean"
    res = detector.process("open the red file i mean the blue file")
    assert res == "<original>open the red file</original> <correction>i mean the blue file</correction>"

    # "scratch that"
    res = detector.process("send the email scratch that save it as draft")
    assert res == "<original>send the email</original> <correction>scratch that save it as draft</correction>"

    # "no wait"
    res = detector.process("delete row two no wait row three")
    assert res == "<original>delete row two</original> <correction>no wait row three</correction>"


def test_backtrack_no_marker_returns_unchanged():
    text = "this is a standard sentence without any self corrections"
    assert backtrack_detector.process(text) == text


def test_backtrack_marker_at_edges():
    # Marker at very start (no 'before' text)
    assert backtrack_detector.process("actually we should leave") == "actually we should leave"

    # Marker at very end (no 'after' text)
    assert backtrack_detector.process("we should leave actually") == "we should leave actually"


def test_backtrack_multiple_markers_uses_last():
    # If multiple markers exist, it matches the last one
    res = backtrack_detector.process("meet at two wait meet at three actually four")
    assert res == "<original>meet at two wait meet at three</original> <correction>actually four</correction>"
