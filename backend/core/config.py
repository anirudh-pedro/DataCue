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

# Ensure third-party SDKs receive the environment variables they expect.
# Our .env uses `groq_api`, but the Groq SDK looks for `GROQ_API_KEY`.
if os.getenv("groq_api") and not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = os.environ["groq_api"]


class Settings:
    """Centralised access to runtime configuration."""

    groq_api_key: Optional[str]
    mongo_uri: Optional[str]
    email_user: Optional[str]
    email_password: Optional[str]
    email_smtp_host: str
    email_smtp_port: int
    email_use_tls: bool
    email_use_ssl: bool
    email_transport: str
    otp_expiry_seconds: int
    email_from_name: Optional[str]

    def __init__(self) -> None:
        self.groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("groq_api")
        self.mongo_uri = os.getenv("MONGO_URI") or os.getenv("mongo_uri")
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_APP_PASSWORD")
        self.email_smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        self.email_smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.email_use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() in {"1", "true", "yes"}
        self.email_use_ssl = os.getenv("EMAIL_USE_SSL", "false").lower() in {"1", "true", "yes"}
        self.email_transport = os.getenv("EMAIL_TRANSPORT", "smtp").lower()
        self.otp_expiry_seconds = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))
        self.email_from_name = os.getenv("EMAIL_FROM_NAME", "DataCue")

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
