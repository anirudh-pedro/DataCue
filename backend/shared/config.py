"""Shared configuration helpers for the orchestrator layer."""

from functools import lru_cache
from typing import Optional

from core.config import get_settings as _get_core_settings, Settings as _CoreSettings


class AppConfig:
    """Expose orchestrator-friendly configuration accessors."""

    def __init__(self, settings: _CoreSettings) -> None:
        self._settings = settings

    @property
    def groq_api_key(self) -> Optional[str]:
        return self._settings.groq_api_key

    @property
    def mongo_uri(self) -> Optional[str]:
        return self._settings.mongo_uri

    @property
    def has_mongo(self) -> bool:
        return self._settings.has_mongo

    @property
    def has_groq(self) -> bool:
        return self._settings.has_groq

    @property
    def firebase_credentials_file(self) -> Optional[str]:
        return self._settings.firebase_credentials_file

    @property
    def firebase_service_account(self) -> Optional[str]:
        return self._settings.firebase_service_account

    @property
    def firebase_project_id(self) -> Optional[str]:
        return self._settings.firebase_project_id

    @property
    def disable_firebase_auth(self) -> bool:
        return self._settings.disable_firebase_auth

    @property
    def firebase_auth_emulator_host(self) -> Optional[str]:
        return self._settings.firebase_auth_emulator_host

    @property
    def has_firebase_credentials(self) -> bool:
        return self._settings.has_firebase_credentials


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return AppConfig(_get_core_settings())
