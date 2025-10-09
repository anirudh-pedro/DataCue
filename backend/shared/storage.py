"""Centralised file storage utilities for datasets, models, and metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "saved_models"
METADATA_DIR = BASE_DIR / "metadata"

for directory in (DATA_DIR, MODELS_DIR, METADATA_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def dataset_path(name: str) -> Path:
    return DATA_DIR / f"{name}.csv"


def save_dataset(name: str, content: bytes) -> Path:
    path = dataset_path(name)
    path.write_bytes(content)
    return path


def model_path(model_id: str) -> Path:
    return MODELS_DIR / f"{model_id}.pkl"


def metadata_path(model_id: str) -> Path:
    return METADATA_DIR / f"{model_id}.json"


def save_metadata(model_id: str, metadata: Dict[str, Any]) -> Path:
    path = metadata_path(model_id)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    return path


def load_metadata(model_id: str) -> Optional[Dict[str, Any]]:
    path = metadata_path(model_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
