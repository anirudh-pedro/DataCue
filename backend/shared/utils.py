"""General utility helpers used across orchestrator services."""

from datetime import date, datetime
import re
from typing import Any, Dict, Iterable


_SLUG_PATTERN = re.compile(r"[^A-Za-z0-9_-]+")


def slugify(value: str, fallback: str = "item") -> str:
    slug = _SLUG_PATTERN.sub("_", value).strip("_")
    return slug or fallback


def clean_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise response payloads for FastAPI/Pydantic serialization."""
    return {
        key: _ensure_serializable(value)
        for key, value in data.items()
        if value is not None
    }


def _ensure_serializable(value: Any) -> Any:
    """Convert common non-serializable types (NumPy, Pandas, sets) to JSON friendly values."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {key: _ensure_serializable(val) for key, val in value.items() if val is not None}

    if isinstance(value, (list, tuple)):
        return [_ensure_serializable(item) for item in value]

    if isinstance(value, set):
        return [_ensure_serializable(item) for item in value]

    module = type(value).__module__
    if module and module.startswith("numpy"):
        if hasattr(value, "item"):
            return _ensure_serializable(value.item())
        if hasattr(value, "tolist"):
            return _ensure_serializable(value.tolist())

    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        return _ensure_serializable(value.to_dict())

    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [_ensure_serializable(item) for item in value]

    return str(value)
