"""Service layer for dashboard generation."""

from typing import Any, Dict, List, Optional
import pandas as pd

from agents.dashboard_agent import DashboardAgent
from core.gridfs_service import get_gridfs_service
from services.dataset_service import get_dataset_service


class DashboardService:
    """Handles dashboard generation using LLM"""
    
    def __init__(self) -> None:
        self._agent = DashboardAgent()
        self._dataset_service = get_dataset_service()

    def generate(
        self, 
        data: List[Dict[str, Any]] = None, 
        gridfs_id: str = None,
        session_id: str = None,
        dataset_id: str = None,
        metadata: Dict[str, Any] = None,
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a dashboard from data
        
        Args:
            data: Dataset records (optional if gridfs_id or session_id provided)
            gridfs_id: GridFS file ID (optional)
            session_id: Session ID for MongoDB data (optional)
            dataset_id: Dataset ID in MongoDB (optional)
            metadata: Column metadata from ingestion
            user_prompt: Optional user guidance for dashboard
            
        Returns:
            Dashboard configuration with charts and data
        """
        # Get data from appropriate source
        if data:
            df = pd.DataFrame(data)
        elif gridfs_id:
            df = self._load_from_gridfs(gridfs_id)
        elif session_id and self._dataset_service.is_enabled:
            df = self._load_from_mongo(session_id, dataset_id)
        else:
            return {
                "status": "error",
                "message": "No data source provided. Provide data, gridfs_id, or session_id."
            }
        
        if df is None or df.empty:
            return {
                "status": "error",
                "message": "Failed to load data or data is empty"
            }
        
        # Extract metadata if not provided
        if not metadata:
            metadata = self._extract_metadata(df)
        
        # Generate dashboard
        result = self._agent.generate_dashboard(
            metadata=metadata,
            data=df.to_dict(orient='records'),
            user_prompt=user_prompt
        )
        
        return result
    
    def _load_from_gridfs(self, gridfs_id: str) -> Optional[pd.DataFrame]:
        """Load data from GridFS"""
        try:
            gridfs_service = get_gridfs_service()
            file_stream = gridfs_service.get_file_stream(gridfs_id)
            return pd.read_csv(file_stream)
        except Exception:
            return None
    
    def _load_from_mongo(self, session_id: str, dataset_id: str = None) -> Optional[pd.DataFrame]:
        """Load data from MongoDB"""
        try:
            rows = self._dataset_service.get_all_rows(
                session_id=session_id,
                dataset_id=dataset_id
            )
            if rows:
                return pd.DataFrame(rows)
            return None
        except Exception:
            return None
    
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
