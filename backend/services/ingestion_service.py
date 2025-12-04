"""Service layer wrapping the File Ingestion Agent."""

from typing import Any, Dict, Optional
import uuid

import pandas as pd

from agents.file_ingestion_agent.ingestion_agent import FileIngestionAgent
from shared.storage import save_dataset, dataset_path
from shared.utils import slugify
from core.gridfs_service import get_gridfs_service
from services.dataset_service import get_dataset_service


class IngestionService:
    def __init__(self) -> None:
        self._agent = FileIngestionAgent()
        self._dataset_service = get_dataset_service()

    def ingest_file(self, filename: str, content: bytes, sheet_name: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        dataset_name = slugify(filename.rsplit(".", 1)[0], fallback="dataset")
        
        # Save locally for processing
        save_dataset(dataset_name, content)
        path = dataset_path(dataset_name)
        
        # Save to GridFS for persistence
        gridfs_service = get_gridfs_service()
        gridfs_id = gridfs_service.save_file(
            filename=f"{dataset_name}.csv",
            content=content,
            metadata={
                "original_filename": filename,
                "dataset_name": dataset_name
            }
        )
        
        # Process file with agent
        result = self._agent.ingest_file(str(path), sheet_name=sheet_name)
        metadata = result.get("metadata", {}) or {}
        if metadata.get("columns"):
            metadata["columns_metadata"] = {
                column_info.get("name"): column_info
                for column_info in metadata["columns"]
                if isinstance(column_info, dict) and column_info.get("name")
            }
        quality_info = metadata.get("data_quality_score")
        if isinstance(quality_info, dict):
            overall = quality_info.get("overall_score")
            if overall is None:
                scores = quality_info.get("scores")
                if isinstance(scores, dict) and scores:
                    numeric_scores = [value for value in scores.values() if isinstance(value, (int, float))]
                    if numeric_scores:
                        overall = sum(numeric_scores) / len(numeric_scores)
            if isinstance(overall, (int, float)):
                metadata["data_quality_score"] = float(overall)
            metadata.setdefault("quality_components", quality_info.get("scores", {}))
            metadata.setdefault("quality_issues", quality_info.get("issues", []))
            rating = quality_info.get("rating")
            if rating:
                metadata.setdefault("data_quality_rating", rating)
        if metadata:
            result["metadata"] = metadata
        result["dataset_name"] = dataset_name
        result["gridfs_id"] = gridfs_id
        
        # Build dataframe for MongoDB storage if available
        dataframe = result.get("dataframe")
        if dataframe is None and isinstance(result.get("data"), list) and result["data"]:
            try:
                dataframe = pd.DataFrame(result["data"])
            except Exception:  # pragma: no cover - defensive conversion safeguard
                dataframe = None

        # Store dataset rows in MongoDB for Groq querying
        if self._dataset_service.is_enabled and dataframe is not None and not dataframe.empty:
            dataset_id = str(uuid.uuid4())
            effective_session_id = session_id or dataset_id  # Use provided session or generate one
            
            store_result = self._dataset_service.store_dataset(
                session_id=effective_session_id,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                dataframe=dataframe,
                metadata=metadata
            )
            
            if store_result.get("success"):
                result["dataset_id"] = dataset_id
                result["session_id"] = effective_session_id
                result["mongo_storage"] = {
                    "enabled": True,
                    "session_id": effective_session_id,
                    "dataset_id": dataset_id,
                    "rows_stored": store_result.get("rows_stored"),
                }
            else:
                result["mongo_storage"] = {
                    "enabled": False,
                    "error": store_result.get("error")
                }
        else:
            result["mongo_storage"] = {"enabled": False}
        
        # Ensure we surface identifiers when MongoDB storage is disabled
        if session_id and not result.get("session_id"):
            result["session_id"] = session_id

        return result
