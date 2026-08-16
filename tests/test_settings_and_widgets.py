from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from src.config.manager import ConfigManager
from src.gui.settings import SettingsWindow
from src.gui.widgets.dictionary_editor import DictionaryEditor
from src.gui.widgets.snippet_editor import SnippetEditor
from src.gui.widgets.stats_dialog import StatsDialog
from src.gui.widgets.style_editor import StyleEditor


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_dictionary_editor_crud(tmp_path, qapp):
    cfg = ConfigManager(config_path=tmp_path / "config.json")
    cfg.set("dictionary", ["existing_term"])

    editor = DictionaryEditor(cfg)
    assert editor.list_widget.count() == 1

    # Add new word
    editor.word_input.setText("kubernetes")
    editor.add_word()
    assert "kubernetes" in cfg.get("dictionary")
    assert editor.list_widget.count() == 2
    assert editor.word_input.text() == ""

    # Remove word
    editor.list_widget.setCurrentRow(0)
    editor.remove_word()
    assert editor.list_widget.count() == 1
    assert "existing_term" not in cfg.get("dictionary")
    editor.close()


def test_dictionary_editor_load_industry_pack(tmp_path, qapp):
    cfg = ConfigManager(config_path=tmp_path / "config.json")
    cfg.set("dictionary", [])

    editor = DictionaryEditor(cfg)
    editor.pack_dropdown.setCurrentText("Medical")
    editor.load_industry_pack()

    dict_words = cfg.get("dictionary", [])
    assert len(dict_words) > 0
    assert "hydrochlorothiazide" in dict_words
    assert editor.list_widget.count() == len(dict_words)
    editor.close()


def test_snippet_editor_crud(tmp_path, qapp):
    cfg = ConfigManager(config_path=tmp_path / "config.json")
    cfg.set("snippets", {"sig": "best regards"})

    editor = SnippetEditor(cfg)
    assert editor.table_widget.rowCount() == 1

    # Add snippet
    editor.trigger_input.setText("addr")
    editor.expansion_input.setPlainText("123 Main St")
    editor.add_snippet()

    snippets = cfg.get("snippets")
    assert snippets["addr"] == "123 Main St"
    assert editor.table_widget.rowCount() == 2

    # Remove snippet
    editor.table_widget.setCurrentCell(0, 0)
    editor.remove_snippet()
    assert editor.table_widget.rowCount() == 1
    editor.close()


def test_style_editor_crud(tmp_path, qapp):
    cfg = ConfigManager(config_path=tmp_path / "config.json")
    cfg.set("app_styles", {"slack.exe": "casual"})

    editor = StyleEditor(cfg)
    assert editor.table_widget.rowCount() == 1

    # Add style mapping
    editor.process_input.setText("code.exe")
    editor.profile_combo.setCurrentText("technical")
    editor.add_style_mapping()

    styles = cfg.get("app_styles")
    assert styles["code.exe"] == "technical"
    assert editor.table_widget.rowCount() == 2

    # Remove style mapping
    editor.table_widget.setCurrentCell(0, 0)
    editor.remove_style_mapping()
    assert editor.table_widget.rowCount() == 1
    editor.close()


@patch("src.gui.widgets.stats_dialog.stats_store.get_totals")
def test_stats_dialog(mock_totals, qapp):
    mock_totals.return_value = {
        "total_sessions": 42,
        "total_words": 1500,
        "total_chars": 8000,
        "total_duration_sec": 600.0,
        "avg_wpm": 150.0
    }
    dialog = StatsDialog()
    assert dialog.windowTitle() == "Usage Insights"
    dialog.close()


def test_settings_window_save(tmp_path, qapp):
    cfg = ConfigManager(config_path=tmp_path / "config.json")
    settings = SettingsWindow(cfg)

    saved_payload = []
    settings.settings_saved.connect(lambda d: saved_payload.append(d))

    settings.hotkey_input.setText("<ctrl>+<shift>+d")
    settings.vad_input.setValue(0.7)
    settings.model_input.setCurrentText("small")
    settings.whisper_mode_input.setChecked(True)
    settings.hibernation_checkbox.setChecked(False)

    settings.save_settings()

    assert cfg.get("hotkey") == "<ctrl>+<shift>+d"
    assert cfg.get("vad_threshold") == 0.7
    assert cfg.get("model_selection") == "small"
    assert cfg.get("whisper_mode") is True
    assert cfg.get("enable_hibernation") is False
    assert len(saved_payload) == 1
    assert saved_payload[0]["hotkey"] == "<ctrl>+<shift>+d"
    assert saved_payload[0]["enable_hibernation"] is False
    settings.close()


def test_settings_window_hibernation_toggled(tmp_path, qapp):
    cfg = ConfigManager(config_path=tmp_path / "config.json")
    settings = SettingsWindow(cfg)

    settings.hibernation_checkbox.setChecked(False)
    assert cfg.get("enable_hibernation") is False

    settings.hibernation_checkbox.setChecked(True)
    assert cfg.get("enable_hibernation") is True
    settings.close()
