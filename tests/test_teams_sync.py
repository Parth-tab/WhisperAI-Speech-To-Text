from unittest.mock import patch

from src.config.manager import ConfigManager
from src.teams.api_client import TeamAPIClient
from src.teams.auth import AuthManager
from src.teams.sync import TeamSyncManager


def test_auth_manager_login_logout():
    auth = AuthManager()
    assert auth.is_authenticated is False
    assert auth.user_email is None

    # Login failure on empty
    assert auth.login("", "") is False
    assert auth.is_authenticated is False

    # Login success
    assert auth.login("user@example.com", "secret123") is True
    assert auth.is_authenticated is True
    assert auth.user_email == "user@example.com"

    # Logout
    auth.logout()
    assert auth.is_authenticated is False
    assert auth.user_email is None


def test_team_api_client_token():
    client = TeamAPIClient()
    assert client.auth_token is None
    client.set_token("token_abc")
    assert client.auth_token == "token_abc"


def test_team_sync_disabled():
    cfg = ConfigManager()
    cfg.set("team_sync_enabled", False)
    sync = TeamSyncManager(cfg)
    assert sync.sync_all() is False


@patch("src.teams.sync.team_api")
def test_team_sync_enabled_merges_dictionary_and_snippets(mock_api):
    cfg = ConfigManager()
    cfg.set("team_sync_enabled", True)
    cfg.set("dictionary", ["local_word1", "common_word"])
    cfg.set("snippets", {"sig": "local signature", "my_link": "https://local.com"})

    mock_api.pull_dictionary.return_value = ["remote_word1", "common_word"]
    mock_api.pull_snippets.return_value = {"sig": "remote signature", "team_link": "https://team.com"}

    sync = TeamSyncManager(cfg)
    assert sync.sync_all() is True

    # Check merged dictionary (deduplicated)
    dict_result = cfg.get("dictionary")
    assert "local_word1" in dict_result
    assert "remote_word1" in dict_result
    assert "common_word" in dict_result

    # Check merged snippets (local overrides remote for 'sig')
    snippet_result = cfg.get("snippets")
    assert snippet_result["sig"] == "local signature"
    assert snippet_result["team_link"] == "https://team.com"
    assert snippet_result["my_link"] == "https://local.com"
