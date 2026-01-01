"""Service for handling chat queries using the ChatAgent."""

from typing import Any, Dict, List, Optional
import pandas as pd

from agents.chat_agent import ChatAgent
from services.dataset_service import get_dataset_service



class ChatQueryService:
    """Handles natural language queries on datasets"""
    
    def __init__(self) -> None:
        self._agent = ChatAgent()
        self._dataset_service = get_dataset_service()
    
    def ask(
        self,
        question: str,
        session_id: str = None,
        dataset_id: str = None,
        gridfs_id: str = None,
        data: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Answer a natural language question about the dataset
        
        Args:
            question: User's question
            session_id: Session ID for MongoDB data
            dataset_id: Dataset ID in MongoDB
            gridfs_id: GridFS file ID
            data: Direct data records
            metadata: Column metadata
            
        Returns:
            Answer with result data and insight
        """
        # Get data from appropriate source
        if data:
            df = pd.DataFrame(data)
        elif session_id and self._dataset_service.is_enabled:
            rows = self._dataset_service.get_all_rows(
                session_id=session_id,
                dataset_id=dataset_id
            )
            if not rows:
                return {
                    "status": "error",
                    "message": "No data found for this session"
                }
            df = pd.DataFrame(rows)
        elif gridfs_id:
            # gridfs_id is now an alias for file_id in the new system
            from core.file_service import get_file_service
            file_service = get_file_service()
            
            # Retrieve file content directly
            file_data = file_service.get_file(gridfs_id)
            if file_data and file_data.get('content'):
                from io import BytesIO
                file_stream = BytesIO(file_data['content'])
                df = pd.read_csv(file_stream)
            else:
                return {
                    "status": "error",
                    "message": "File not found"
                }
        else:
            return {
                "status": "error",
                "message": "No data source provided"
            }
        
        if df.empty:
            return {
                "status": "error",
                "message": "Dataset is empty"
            }
        
        # Extract metadata if not provided
        if not metadata:
            metadata = self._extract_metadata(df)
        
        # Use chat agent to answer
        result = self._agent.ask(
            question=question,
            metadata=metadata,
            data=df.to_dict(orient='records')
        )
        
        return result
    
    def _extract_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract basic metadata from dataframe"""
        columns = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                dtype = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                dtype = "datetime"
            else:
                dtype = "categorical"
            
            columns.append({
                "name": col,
                "type": dtype,
                "unique_count": int(df[col].nunique()),
                "null_count": int(df[col].isnull().sum())
            })
        
        return {
            "columns": columns,
            "row_count": len(df),
            "column_count": len(df.columns)
        }


# Singleton instance
_chat_query_service: Optional[ChatQueryService] = None


def get_chat_query_service() -> ChatQueryService:
    """Get singleton ChatQueryService instance"""
    global _chat_query_service
    if _chat_query_service is None:
        _chat_query_service = ChatQueryService()
    return _chat_query_service
