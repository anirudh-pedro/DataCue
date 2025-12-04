"""MongoDB-backed dataset row storage for Groq query execution."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd
from pymongo import MongoClient
from pymongo.collection import Collection

from core.config import get_settings

LOGGER = logging.getLogger(__name__)


class DatasetService:
    """Store and query dataset rows in MongoDB."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: Optional[MongoClient] = None
        self._collection: Optional[Collection] = None
        self._datasets_meta: Optional[Collection] = None
        
        if self._settings.has_mongo:
            try:
                self._client = MongoClient(self._settings.mongo_uri)
                db = self._client.get_database()
                self._collection = db["session_dataset_rows"]
                self._datasets_meta = db["session_datasets_meta"]
                
                # Create indexes for efficient querying
                self._collection.create_index([("session_id", 1), ("dataset_id", 1)])
                self._collection.create_index([("dataset_id", 1)])
                self._datasets_meta.create_index([("session_id", 1)])
                self._datasets_meta.create_index([("session_id", 1), ("dataset_id", 1)])
                self._datasets_meta.create_index([("session_id", 1), ("created_at", -1)])
                
                LOGGER.info("DatasetService initialized with MongoDB")
            except Exception as exc:
                LOGGER.error("Failed to initialize MongoDB for DatasetService: %s", exc)
                self._client = None
        else:
            LOGGER.info("DatasetService disabled (no MONGO_URI configured)")

    @property
    def is_enabled(self) -> bool:
        """Check if MongoDB storage is available."""
        return self._client is not None and self._collection is not None

    def store_dataset(
        self,
        *,
        session_id: str,
        dataset_id: str,
        dataset_name: str,
        dataframe: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store cleaned dataset rows in MongoDB with sanitized column names."""
        if not self.is_enabled:
            return {"success": False, "error": "MongoDB storage not configured"}

        # Sanitize column names for MongoDB (no $, ., or starting with numbers)
        column_map = {}
        sanitized_columns = []
        
        for col in dataframe.columns:
            sanitized = self._sanitize_column_name(col)
            column_map[col] = sanitized
            sanitized_columns.append(sanitized)
        
        # Rename dataframe columns
        df_sanitized = dataframe.rename(columns=column_map)
        
        # Convert to documents
        documents = []
        for idx, row in df_sanitized.iterrows():
            doc = {
                "session_id": session_id,
                "dataset_id": dataset_id,
                "row_index": int(idx),
            }
            # Add each column value
            for col in sanitized_columns:
                value = row[col]
                # Convert numpy/pandas types to Python native types
                if pd.isna(value):
                    doc[col] = None
                elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                    doc[col] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                else:
                    doc[col] = self._convert_to_native_type(value)
            
            documents.append(doc)
        
        try:
            # Clear any existing data previously associated with this session
            self._collection.delete_many({
                "session_id": session_id
            })
            self._datasets_meta.delete_many({"session_id": session_id})
            
            # Insert new documents
            if documents:
                self._collection.insert_many(documents)
            
            # Store metadata
            from datetime import datetime, timezone
            
            meta_doc = {
                "session_id": session_id,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "row_count": len(documents),
                "column_map": column_map,  # original -> sanitized mapping
                "columns": list(column_map.values()),  # sanitized column names
                "column_types": {col: str(dataframe[orig_col].dtype) for orig_col, col in column_map.items()},
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc),
            }
            
            self._datasets_meta.insert_one(meta_doc)
            
            LOGGER.info(
                "Stored %d rows for session=%s dataset=%s",
                len(documents), session_id, dataset_id
            )
            
            return {
                "success": True,
                "rows_stored": len(documents),
                "columns": len(sanitized_columns),
                "column_map": column_map,
            }
            
        except Exception as exc:
            LOGGER.exception("Failed to store dataset rows: %s", exc)
            return {"success": False, "error": str(exc)}

    def get_session_dataset(self, session_id: str, dataset_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve dataset metadata for a session.

        Args:
            session_id: Chat/session identifier used when storing the dataset.
            dataset_id: Optional explicit dataset identifier to look up.
        """
        if not self.is_enabled:
            return None
        
        try:
            query: Dict[str, Any] = {"session_id": session_id}
            if dataset_id:
                query["dataset_id"] = dataset_id

            doc = self._datasets_meta.find_one(
                query,
                sort=[("created_at", -1)]  # Sort by creation time descending
            )
            if doc:
                doc.pop("_id", None)
                LOGGER.info(f"Found dataset for session {session_id}: {doc.get('dataset_id')}")
            else:
                LOGGER.warning(f"No dataset found for session: {session_id}")
            return doc
        except Exception as exc:
            LOGGER.error("Failed to fetch dataset metadata: %s", exc)
            return None

    def get_sample_rows(self, *, dataset_id: str, session_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample rows from a dataset."""
        if not self.is_enabled:
            return []
        
        try:
            query: Dict[str, Any] = {"dataset_id": dataset_id}
            if session_id:
                query["session_id"] = session_id
            cursor = self._collection.find(
                query,
                {"_id": 0}
            ).limit(limit)
            
            return list(cursor)
        except Exception as exc:
            LOGGER.error("Failed to fetch sample rows: %s", exc)
            return []

    def run_pipeline(self, session_id: str, dataset_id: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a MongoDB aggregation pipeline scoped to a session/dataset."""
        if not self.is_enabled:
            raise RuntimeError("MongoDB not configured")
        
        try:
            secured_pipeline = self._ensure_security_filters(pipeline, session_id=session_id, dataset_id=dataset_id)
            cursor = self._collection.aggregate(secured_pipeline)
            results = list(cursor)
            
            # Remove MongoDB _id fields
            for doc in results:
                doc.pop("_id", None)
            
            return results
        except Exception as exc:
            LOGGER.exception("Pipeline execution failed: %s", exc)
            raise

    def clear_session_data(self, session_id: str) -> Dict[str, Any]:
        """Delete all dataset rows and metadata for a session."""
        if not self.is_enabled:
            return {"success": False, "error": "MongoDB not configured"}
        
        try:
            rows_deleted = self._collection.delete_many({"session_id": session_id}).deleted_count
            meta_deleted = self._datasets_meta.delete_one({"session_id": session_id}).deleted_count
            
            return {
                "success": True,
                "rows_deleted": rows_deleted,
                "metadata_deleted": meta_deleted > 0,
            }
        except Exception as exc:
            LOGGER.error("Failed to clear session data: %s", exc)
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _sanitize_column_name(name: str) -> str:
        """Sanitize column name for MongoDB field names."""
        # Replace problematic characters
        sanitized = re.sub(r'[^\w]', '_', str(name))
        
        # Ensure doesn't start with number or $
        if sanitized and (sanitized[0].isdigit() or sanitized[0] == '$'):
            sanitized = f"col_{sanitized}"
        
        # Ensure not empty
        if not sanitized:
            sanitized = "column"
        
        return sanitized.lower()

    @staticmethod
    def _convert_to_native_type(value: Any) -> Any:
        """Convert pandas/numpy types to Python native types."""
        if hasattr(value, 'item'):  # numpy types
            return value.item()
        if isinstance(value, (list, dict)):
            return value
        return value

    @staticmethod
    def _ensure_security_filters(
        pipeline: List[Dict[str, Any]],
        *,
        session_id: str,
        dataset_id: str,
    ) -> List[Dict[str, Any]]:
        """Prepend mandatory match stage to keep queries session-scoped."""
        if not isinstance(pipeline, list):
            raise ValueError("Pipeline must be provided as a list of stages")

        guard = {"session_id": session_id, "dataset_id": dataset_id}
        security_stage = {"$match": guard}

        if pipeline and isinstance(pipeline[0], dict) and "$match" in pipeline[0]:
            return [
                {"$match": {"$and": [guard, pipeline[0]["$match"]]}},
                *pipeline[1:],
            ]

        return [security_stage, *pipeline]


_DATASET_SERVICE: Optional[DatasetService] = None


def get_dataset_service() -> DatasetService:
    """Get or create singleton DatasetService instance."""
    global _DATASET_SERVICE
    if _DATASET_SERVICE is None:
        _DATASET_SERVICE = DatasetService()
    return _DATASET_SERVICE
