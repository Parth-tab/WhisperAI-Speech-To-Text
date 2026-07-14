from src.config.manager import ConfigManager


def test_config_manager_defaults(tmp_path):
    config_file = tmp_path / "config.json"
    manager = ConfigManager(config_path=str(config_file))

    assert manager.get("hotkey") == "<ctrl>+<alt>+w"
    assert manager.get("vad_threshold") == 0.5
    assert manager.get("model_selection") == "base"


def test_config_manager_save_load(tmp_path):
    config_file = tmp_path / "config.json"
    manager = ConfigManager(config_path=str(config_file))

    manager.set("hotkey", "<shift>+<space>")
    manager.set("vad_threshold", 0.7)

    # Create new instance to test loading
    manager2 = ConfigManager(config_path=str(config_file))
    assert manager2.get("hotkey") == "<shift>+<space>"
    assert manager2.get("vad_threshold") == 0.7
    assert manager2.get("model_selection") == "base"


def test_config_manager_invalid_load(tmp_path):
    config_file = tmp_path / "config.json"
    # Write invalid json
    with open(config_file, "w") as f:
        f.write("{invalid_json:")

    # Should not crash, should fall back to defaults
    manager = ConfigManager(config_path=str(config_file))
    assert manager.get("hotkey") == "<ctrl>+<alt>+w"
