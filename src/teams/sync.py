from src.teams.api_client import team_api
from src.config.manager import ConfigManager

class TeamSyncManager:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager

    def sync_all(self):
        """
        Scaffold logic for bi-directional sync of dictionaries and snippets.
        Resolves conflicts (e.g. keeping local additions, merging team globals).
        """
        if not self.config.get("team_sync_enabled", False):
            return False

        print("[TeamSync] Starting background sync...")
        
        # 1. Dictionary Sync
        local_dict = self.config.get("dictionary", [])
        team_api.push_dictionary(local_dict)
        remote_dict = team_api.pull_dictionary()
        
        merged_dict = list(set(local_dict + remote_dict))
        if len(merged_dict) != len(local_dict):
            self.config.set("dictionary", merged_dict)
            
        # 2. Snippet Sync
        local_snippets = self.config.get("snippets", {})
        team_api.push_snippets(local_snippets)
        remote_snippets = team_api.pull_snippets()
        
        merged_snippets = {**remote_snippets, **local_snippets} # Local overrides remote
        if merged_snippets != local_snippets:
            self.config.set("snippets", merged_snippets)

        print("[TeamSync] Sync complete.")
        return True
