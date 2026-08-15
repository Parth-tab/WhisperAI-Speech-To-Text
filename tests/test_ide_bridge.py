from unittest.mock import patch

from src.injection.ide_bridge import IDEBridge


@patch("src.injection.ide_bridge.file_indexer")
def test_ide_bridge_process_file_tags_success(mock_indexer):
    mock_indexer.get_workspace_for_pid.return_value = "C:\\Projects\\App"
    mock_indexer.fuzzy_find_file.side_effect = lambda ws, hint: "pipeline.py" if hint == "pipeline" else ""

    bridge = IDEBridge()
    result = bridge.process_file_tags("please look in file pipeline for the bug", pid=1234)
    assert result == "please look @pipeline.py for the bug"


@patch("src.injection.ide_bridge.file_indexer")
def test_ide_bridge_at_file_syntax(mock_indexer):
    mock_indexer.get_workspace_for_pid.return_value = "C:\\Projects\\App"
    mock_indexer.fuzzy_find_file.side_effect = lambda ws, hint: "app.py" if hint == "app" else ""

    bridge = IDEBridge()
    result = bridge.process_file_tags("check at file app", pid=1234)
    assert result == "check @app.py"


def test_ide_bridge_invalid_pid_returns_unchanged():
    bridge = IDEBridge()
    text = "in file pipeline"
    assert bridge.process_file_tags(text, pid=0) == text
    assert bridge.process_file_tags(text, pid=-1) == text


@patch("src.injection.ide_bridge.file_indexer")
def test_ide_bridge_no_workspace_returns_unchanged(mock_indexer):
    mock_indexer.get_workspace_for_pid.return_value = ""
    bridge = IDEBridge()
    text = "in file unknown"
    assert bridge.process_file_tags(text, pid=5678) == text
