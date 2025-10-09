"""Service layer wrapping the File Ingestion Agent."""

from typing import Any, Dict, Optional

from agents.file_ingestion_agent.ingestion_agent import FileIngestionAgent
from shared.storage import save_dataset, dataset_path
from shared.utils import slugify


class IngestionService:
    def __init__(self) -> None:
        self._agent = FileIngestionAgent()

    def ingest_file(self, filename: str, content: bytes, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        dataset_name = slugify(filename.rsplit(".", 1)[0], fallback="dataset")
        save_dataset(dataset_name, content)
        path = dataset_path(dataset_name)
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
        return result
