import os
import time
import pytest
from unittest.mock import patch, MagicMock
from src.utils.file_index import FileIndexer


def test_file_indexer_scan_depth_and_ignore(tmp_path):
    # Setup test workspace directory hierarchy
    ws = tmp_path / "workspace"
    ws.mkdir()
    
    (ws / "main.py").write_text("print('hello')", encoding="utf-8")
    (ws / "config.json").write_text("{}", encoding="utf-8")
    
    # Subdir level 1
    sub1 = ws / "src"
    sub1.mkdir()
    (sub1 / "pipeline.py").write_text("# pipeline", encoding="utf-8")
    
    # Subdir level 2
    sub2 = sub1 / "utils"
    sub2.mkdir()
    (sub2 / "helper.py").write_text("# helper", encoding="utf-8")
    
    # Ignored directories
    git_dir = ws / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref", encoding="utf-8")
    
    node_dir = ws / "node_modules"
    node_dir.mkdir()
    (node_dir / "package.json").write_text("{}", encoding="utf-8")

    indexer = FileIndexer()
    files = indexer.scan_workspace(str(ws))
    
    assert "main.py" in files
    assert "config.json" in files
    assert "pipeline.py" in files
    assert "helper.py" in files
    # Ignored directory files should NOT be present
    assert "HEAD" not in files
    assert "package.json" not in files


def test_file_indexer_cache_ttl(tmp_path):
    ws = tmp_path / "workspace_ttl"
    ws.mkdir()
    (ws / "initial.py").write_text("# init", encoding="utf-8")

    indexer = FileIndexer()
    files1 = indexer.scan_workspace(str(ws))
    assert "initial.py" in files1

    # Add new file without invalidating cache (<60s)
    (ws / "secondary.py").write_text("# sec", encoding="utf-8")
    files2 = indexer.scan_workspace(str(ws))
    assert "secondary.py" not in files2  # Cache hit, secondary not scanned yet

    # Expire cache (>60s)
    indexer.last_scanned[str(ws)] = time.time() - 65
    files3 = indexer.scan_workspace(str(ws))
    assert "secondary.py" in files3


def test_file_indexer_fuzzy_find(tmp_path):
    ws = tmp_path / "workspace_fuzzy"
    ws.mkdir()
    (ws / "pipeline_engine.py").write_text("", encoding="utf-8")
    (ws / "app_mediator.py").write_text("", encoding="utf-8")
    (ws / "data_loader.py").write_text("", encoding="utf-8")

    indexer = FileIndexer()
    
    # Exact / fuzzy match
    assert indexer.fuzzy_find_file(str(ws), "pipeline") == "pipeline_engine.py"
    assert indexer.fuzzy_find_file(str(ws), "app mediator") == "app_mediator.py"
    assert indexer.fuzzy_find_file(str(ws), "data dot loader") == "data_loader.py"
    
    # Non-existent
    assert indexer.fuzzy_find_file(str(ws), "xyz_nonexistent") == ""


@patch("src.utils.file_index.psutil.Process")
def test_file_indexer_get_workspace_for_pid(mock_process):
    mock_process.return_value.cwd.return_value = "C:\\Projects\\MyProject"
    indexer = FileIndexer()
    assert indexer.get_workspace_for_pid(1234) == "C:\\Projects\\MyProject"
    
    # Handle exception gracefully
    mock_process.side_effect = Exception("Process not found")
    assert indexer.get_workspace_for_pid(9999) == ""
