"""Application configuration management."""

import os

from app.constants import (
    DEFAULT_PHOTOROOM_API_URL,
    ENV_PHOTOROOM_API_KEY,
    ENV_PHOTOROOM_API_URL,
)


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        """Initialize settings from environment variables."""
        self.photoroom_api_key = self._get_required_env(ENV_PHOTOROOM_API_KEY)
        self.photoroom_api_url = self._get_required_env(
            ENV_PHOTOROOM_API_URL, DEFAULT_PHOTOROOM_API_URL
        )

    def _get_required_env(self, key: str, default: str | None = None) -> str:
        """Get a required environment variable.

        Args:
            key: Environment variable name
            default: Default value if the environment variable is not set

        Returns:
            Environment variable value

        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key, default)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value


# Global settings instance
settings = Settings()
