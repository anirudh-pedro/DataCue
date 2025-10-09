"""Model registry layer with optional MongoDB persistence."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from shared.config import get_config
from shared import storage


class ModelRegistry:
    """Persist model metadata using MongoDB when available, or filesystem fallback."""

    def __init__(self) -> None:
        config = get_config()
        self._client: Optional[MongoClient] = None
        self._collection = None

        if config.has_mongo:
            try:
                self._client = MongoClient(config.mongo_uri)
                db = self._client.get_default_database() or self._client["datacue"]
                self._collection = db["model_registry"]
            except PyMongoError:
                self._client = None
                self._collection = None

    def register(self, model_id: str, metadata: Dict[str, Any]) -> None:
        record = {
            "model_id": model_id,
            "metadata": metadata,
            "created_at": datetime.utcnow(),
        }
        storage.save_metadata(model_id, metadata)

        if self._collection is not None:
            try:
                self._collection.insert_one(record)
            except PyMongoError:
                pass

    def get(self, model_id: str) -> Optional[Dict[str, Any]]:
        if self._collection is not None:
            try:
                document = self._collection.find_one({"model_id": model_id})
                if document:
                    return document.get("metadata")
            except PyMongoError:
                pass
        return storage.load_metadata(model_id)

    def list_models(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if self._collection is not None:
            try:
                records.extend(
                    {
                        "model_id": doc.get("model_id"),
                        "metadata": doc.get("metadata", {}),
                        "created_at": doc.get("created_at"),
                    }
                    for doc in self._collection.find().sort("created_at", -1)
                )
            except PyMongoError:
                records = []

        if not records:
            # Fallback to filesystem metadata files
            for path in storage.METADATA_DIR.glob("*.json"):
                model_id = path.stem
                metadata = storage.load_metadata(model_id) or {}
                records.append({
                    "model_id": model_id,
                    "metadata": metadata,
                })
        return records
