import logging
import time

from src.teams.api_client import team_api

logger = logging.getLogger("whisperai")


class AuthManager:
    def __init__(self):
        self.is_authenticated = False
        self.user_email = None

    def login(self, email: str, password: str) -> bool:
        """
        Scaffold logic for authenticating a team user.
        """
        logger.info(f"[Auth] Attempting login for {email}...")
        time.sleep(0.5)

        # Mock successful auth
        if email and password:
            self.is_authenticated = True
            self.user_email = email
            team_api.set_token(f"mock_token_for_{email}")
            logger.info("[Auth] Login successful.")
            return True

        logger.warning("[Auth] Login failed.")
        return False

    def logout(self):
        self.is_authenticated = False
        self.user_email = None
        team_api.set_token(None)
        logger.info("[Auth] Logged out.")


auth_manager = AuthManager()
