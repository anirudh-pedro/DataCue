"""General utility helpers used across orchestrator services."""

from datetime import date, datetime
import re
from typing import Any, Dict, Iterable

import math

import numpy as np
import pandas as pd


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
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    if isinstance(value, (str, int, bool)) or value is None:
        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()

    if isinstance(value, dict):
        serialised: Dict[str, Any] = {}
        for key, val in value.items():
            if val is None:
                continue
            safe_key = _ensure_serializable(key)
            if not isinstance(safe_key, (str, int, float, bool)):
                safe_key = str(safe_key)
            serialised[str(safe_key)] = _ensure_serializable(val)
        return serialised

    if isinstance(value, (list, tuple, set)):
        return [_ensure_serializable(item) for item in value if item is not None]

    module = type(value).__module__
    if module and module.startswith("numpy"):
        if isinstance(value, np.generic):
            cast = value.item()
            return _ensure_serializable(cast)
        if hasattr(value, "tolist"):
            return _ensure_serializable(value.tolist())

    if isinstance(value, (pd.Series, pd.Index)):
        return [_ensure_serializable(item) for item in value.tolist()]

    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        return _ensure_serializable(value.to_dict())

    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [_ensure_serializable(item) for item in value]

    # Fallback to string representation to avoid serialization errors
    return str(value)
