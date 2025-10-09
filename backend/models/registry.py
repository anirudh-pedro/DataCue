"""Model registry layer with optional MongoDB persistence."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, MongoClient
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
                self._client = MongoClient(config.mongo_uri, serverSelectionTimeoutMS=2_000)
                db = self._client.get_default_database() or self._client["datacue"]
                self._collection = db["model_registry"]
                self._collection.create_index([("model_id", ASCENDING)], unique=True)
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
                self._collection.replace_one({"model_id": model_id}, record, upsert=True)
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
        records: Dict[str, Dict[str, Any]] = {}
        if self._collection is not None:
            try:
                for doc in self._collection.find().sort("created_at", -1):
                    model_id = doc.get("model_id")
                    if not model_id:
                        continue
                    records[model_id] = {
                        "model_id": model_id,
                        "metadata": doc.get("metadata", {}),
                        "created_at": doc.get("created_at"),
                    }
            except PyMongoError:
                records = {}

        for path in storage.METADATA_DIR.glob("*.json"):
            model_id = path.stem
            if model_id in records:
                continue
            metadata = storage.load_metadata(model_id) or {}
            records[model_id] = {
                "model_id": model_id,
                "metadata": metadata,
            }

        return list(records.values())

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._collection = None

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        self.close()
