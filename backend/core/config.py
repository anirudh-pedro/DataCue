"""Application configuration utilities.

Loads environment variables from `.env` and exposes strongly-typed helpers.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load the .env file located at the project root (next to this module's parent directory).
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)


class Settings:
    """Centralised access to runtime configuration."""

    groq_api_key: Optional[str]
    mongo_uri: Optional[str]
    firebase_credentials_file: Optional[str]
    firebase_service_account: Optional[str]
    firebase_project_id: Optional[str]
    disable_firebase_auth: bool
    firebase_auth_emulator_host: Optional[str]

    def __init__(self) -> None:
        # Standardize on uppercase environment variable names
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.mongo_uri = os.getenv("MONGO_URI")
        self.firebase_credentials_file = os.getenv("FIREBASE_CREDENTIALS_FILE")
        self.firebase_service_account = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        self.firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
        self.disable_firebase_auth = os.getenv("DISABLE_FIREBASE_AUTH", "false").lower() in {"1", "true", "yes"}
        self.firebase_auth_emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_mongo(self) -> bool:
        return bool(self.mongo_uri)

    @property
    def has_firebase_credentials(self) -> bool:
        return bool(self.firebase_credentials_file or self.firebase_service_account)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
