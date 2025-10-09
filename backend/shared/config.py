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


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return AppConfig(_get_core_settings())
