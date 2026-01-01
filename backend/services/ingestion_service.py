"""Service layer wrapping the File Ingestion Agent."""

from typing import Any, Dict, Optional
import uuid
import pandas as pd

from agents.file_ingestion_agent import FileIngestionAgent
from shared.storage import save_dataset, dataset_path
from shared.utils import slugify
from core.file_service import get_file_service
from services.dataset_service import get_dataset_service


class IngestionService:
    """Handles file ingestion, cleaning, and storage"""
    
    def __init__(self) -> None:
        self._agent = FileIngestionAgent()

    def ingest_file(
        self, 
        filename: str, 
        content: bytes, 
        sheet_name: Optional[str] = None, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest a file: parse, clean, fix columns, extract metadata, store
        
        Args:
            filename: Original filename
            content: File content as bytes
            sheet_name: Optional sheet name for Excel files
            session_id: Optional session ID for MongoDB storage
            user_id: Optional user ID for ownership (OTP authenticated)
            
        Returns:
            Ingestion result with data, metadata, and storage info
        """
        dataset_name = slugify(filename.rsplit(".", 1)[0], fallback="dataset")
        
        # Save locally for processing
        save_dataset(dataset_name, content)
        path = dataset_path(dataset_name)
        
        # Save to FileService for persistence
        file_service = get_file_service()
        file_id = file_service.save_file(
            filename=f"{dataset_name}.csv",
            content=content,
            session_id=session_id,
            content_type="text/csv",
            metadata={
                "original_filename": filename,
                "dataset_name": dataset_name
            }
        )
        
        # Process file with agent (includes LLM column fixing)
        result = self._agent.ingest(str(path), sheet_name=sheet_name)
        
        if result.get("status") != "success":
            return result
        
        # Add identifiers
        result["dataset_name"] = dataset_name
        result["file_id"] = file_id
        result["gridfs_id"] = file_id  # Alias for frontend compatibility
        
        # Store in PostgreSQL
        data = result.get("data", [])
        dataset_service = get_dataset_service()
        if data and dataset_service.is_enabled:
            try:
                dataframe = pd.DataFrame(data)
                dataset_id = uuid.uuid4().hex
                effective_session_id = session_id or dataset_id
                
                store_result = dataset_service.store_dataset(
                    session_id=effective_session_id,
                    dataset_id=dataset_id,
                    dataset_name=dataset_name,
                    dataframe=dataframe,
                    metadata=result.get("metadata", {}),
                    user_id=user_id
                )
                
                if store_result.get("success"):
                    result["dataset_id"] = dataset_id
                    result["session_id"] = effective_session_id
                    result["mongo_storage"] = {
                        "enabled": True,
                        "rows_stored": store_result.get("rows_stored")
                    }
                else:
                    result["mongo_storage"] = {"enabled": False, "error": store_result.get("error")}
            except Exception as e:
                result["mongo_storage"] = {"enabled": False, "error": str(e)}
        else:
            result["mongo_storage"] = {"enabled": False}
            if session_id:
                result["session_id"] = session_id
        
        return result
