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

    def __init__(self) -> None:
        # Standardize on uppercase environment variable names
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.mongo_uri = os.getenv("MONGO_URI")

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_mongo(self) -> bool:
        return bool(self.mongo_uri)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
