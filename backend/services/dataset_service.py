"""PostgreSQL-backed dataset storage for query execution."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd
from sqlalchemy import desc, func

from core.database import get_db_session
from core.models import Dataset, DatasetRow

LOGGER = logging.getLogger(__name__)


class DatasetService:
    """Store and query dataset rows in PostgreSQL."""

    def __init__(self) -> None:
        LOGGER.info("DatasetService initialized with PostgreSQL")

    @property
    def is_enabled(self) -> bool:
        """Check if database storage is available."""
        return True  # Always enabled with SQLAlchemy

    def store_dataset(
        self,
        *,
        session_id: str,
        dataset_id: Optional[str] = None,
        dataset_name: str,
        dataframe: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store cleaned dataset rows in PostgreSQL."""
        if dataset_id is None:
            dataset_id = uuid4().hex
        
        try:
            with get_db_session() as db:
                # Clear any existing data for this session
                existing_datasets = db.query(Dataset).filter(
                    Dataset.session_id == session_id
                ).all()
                
                for ds in existing_datasets:
                    db.delete(ds)
                
                # Flush to ensure cascade deletes are complete
                db.flush()
                
                # Build column info
                columns_info = []
                column_types = {}
                
                for col in dataframe.columns:
                    dtype = str(dataframe[col].dtype)
                    col_type = "numeric" if pd.api.types.is_numeric_dtype(dataframe[col]) else "categorical"
                    
                    columns_info.append({
                        "name": col,
                        "type": col_type,
                        "dtype": dtype,
                    })
                    column_types[col] = dtype
                
                # Create dataset metadata
                dataset = Dataset(
                    id=dataset_id,
                    session_id=session_id,
                    user_id=user_id,
                    name=dataset_name,
                    row_count=len(dataframe),
                    columns=columns_info,
                    column_types=column_types,
                    metadata_=metadata or {},
                )
                db.add(dataset)
                
                # Store rows in batches
                batch_size = 1000
                rows_stored = 0
                
                for start_idx in range(0, len(dataframe), batch_size):
                    end_idx = min(start_idx + batch_size, len(dataframe))
                    batch_df = dataframe.iloc[start_idx:end_idx]
                    
                    for idx, row in batch_df.iterrows():
                        # Convert row to dict with native Python types
                        row_data = {}
                        for col in dataframe.columns:
                            value = row[col]
                            if pd.isna(value):
                                row_data[col] = None
                            elif hasattr(value, 'item'):  # numpy type
                                row_data[col] = value.item()
                            elif hasattr(value, 'isoformat'):  # datetime
                                row_data[col] = value.isoformat()
                            else:
                                row_data[col] = value
                        
                        dataset_row = DatasetRow(
                            dataset_id=dataset_id,
                            row_index=int(idx),
                            data=row_data,
                        )
                        db.add(dataset_row)
                        rows_stored += 1
                    
                    # Flush batch
                    db.flush()
                
                LOGGER.info(
                    f"Stored {rows_stored} rows for session={session_id} dataset={dataset_id}"
                )
                
                return {
                    "success": True,
                    "rows_stored": rows_stored,
                    "columns": len(dataframe.columns),
                    "dataset_id": dataset_id,
                }
                
        except Exception as exc:
            LOGGER.exception(f"Failed to store dataset rows: {exc}")
            return {"success": False, "error": str(exc)}

    def verify_ownership(
        self, 
        session_id: str, 
        user_id: str, 
        dataset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify that a user owns a dataset."""
        try:
            with get_db_session() as db:
                query = db.query(Dataset).filter(Dataset.session_id == session_id)
                if dataset_id:
                    query = query.filter(Dataset.id == dataset_id)
                
                dataset = query.first()
                
                if not dataset:
                    return {"authorized": False, "reason": "Dataset not found"}
                
                # Check ownership
                if dataset.user_id is None:
                    # Legacy dataset - assign ownership
                    dataset.user_id = user_id
                    LOGGER.info(f"Assigned ownership of dataset {session_id} to {user_id}")
                    return {"authorized": True, "reason": "Legacy dataset (ownership assigned)"}
                
                if dataset.user_id == user_id:
                    return {"authorized": True, "reason": None}
                else:
                    return {"authorized": False, "reason": "User does not own this dataset"}
                    
        except Exception as exc:
            LOGGER.error(f"Failed to verify dataset ownership: {exc}")
            return {"authorized": False, "reason": f"Verification error: {str(exc)}"}

    def get_session_dataset(
        self, 
        session_id: str, 
        dataset_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve dataset metadata for a session."""
        try:
            with get_db_session() as db:
                query = db.query(Dataset).filter(Dataset.session_id == session_id)
                if dataset_id:
                    query = query.filter(Dataset.id == dataset_id)
                
                dataset = query.order_by(desc(Dataset.created_at)).first()
                
                if not dataset:
                    LOGGER.warning(f"No dataset found for session: {session_id}")
                    return None
                
                LOGGER.info(f"Found dataset for session {session_id}: {dataset.id}")
                return dataset.to_dict()
                
        except Exception as exc:
            LOGGER.error(f"Failed to fetch dataset metadata: {exc}")
            return None

    def get_all_rows(
        self, 
        session_id: str, 
        dataset_id: Optional[str] = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """Get all rows from a dataset."""
        try:
            # Get dataset ID if not provided
            if not dataset_id:
                meta = self.get_session_dataset(session_id)
                if meta:
                    dataset_id = meta.get("dataset_id")
                else:
                    return []
            
            with get_db_session() as db:
                rows = db.query(DatasetRow).filter(
                    DatasetRow.dataset_id == dataset_id
                ).order_by(DatasetRow.row_index).limit(limit).all()
                
                return [row.data for row in rows]
                
        except Exception as exc:
            LOGGER.error(f"Failed to fetch all rows: {exc}")
            return []

    def get_sample_rows(
        self, 
        *, 
        dataset_id: str, 
        session_id: Optional[str] = None, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get sample rows from a dataset."""
        try:
            with get_db_session() as db:
                rows = db.query(DatasetRow).filter(
                    DatasetRow.dataset_id == dataset_id
                ).limit(limit).all()
                
                return [row.data for row in rows]
                
        except Exception as exc:
            LOGGER.error(f"Failed to fetch sample rows: {exc}")
            return []

    def clear_session_data(self, session_id: str) -> Dict[str, Any]:
        """Delete all dataset rows and metadata for a session."""
        try:
            with get_db_session() as db:
                datasets = db.query(Dataset).filter(
                    Dataset.session_id == session_id
                ).all()
                
                rows_deleted = 0
                for dataset in datasets:
                    row_count = db.query(DatasetRow).filter(
                        DatasetRow.dataset_id == dataset.id
                    ).delete()
                    rows_deleted += row_count
                    db.delete(dataset)
                
                return {
                    "success": True,
                    "rows_deleted": rows_deleted,
                    "datasets_deleted": len(datasets),
                }
                
        except Exception as exc:
            LOGGER.error(f"Failed to clear session data: {exc}")
            return {"success": False, "error": str(exc)}

    def run_aggregation(
        self, 
        session_id: str, 
        dataset_id: str, 
        group_by: Optional[str] = None,
        aggregate_column: Optional[str] = None,
        aggregate_func: str = "sum",
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run a simple aggregation query on the dataset.
        
        This replaces MongoDB's aggregation pipeline with a Python-based approach
        since complex aggregations on JSONB require PostgreSQL-specific queries.
        """
        try:
            # Get all rows and use pandas for aggregation
            rows = self.get_all_rows(session_id, dataset_id)
            if not rows:
                return []
            
            df = pd.DataFrame(rows)
            
            # Apply filters if provided
            if filters:
                for col, value in filters.items():
                    if col in df.columns:
                        df = df[df[col] == value]
            
            # Perform aggregation
            if group_by and aggregate_column:
                if group_by not in df.columns or aggregate_column not in df.columns:
                    return []
                
                if aggregate_func == "sum":
                    result = df.groupby(group_by)[aggregate_column].sum()
                elif aggregate_func == "avg" or aggregate_func == "mean":
                    result = df.groupby(group_by)[aggregate_column].mean()
                elif aggregate_func == "count":
                    result = df.groupby(group_by)[aggregate_column].count()
                elif aggregate_func == "min":
                    result = df.groupby(group_by)[aggregate_column].min()
                elif aggregate_func == "max":
                    result = df.groupby(group_by)[aggregate_column].max()
                else:
                    result = df.groupby(group_by)[aggregate_column].sum()
                
                result = result.reset_index()
                return result.to_dict('records')
            
            elif aggregate_column:
                if aggregate_column not in df.columns:
                    return []
                
                if aggregate_func == "sum":
                    value = df[aggregate_column].sum()
                elif aggregate_func == "avg" or aggregate_func == "mean":
                    value = df[aggregate_column].mean()
                elif aggregate_func == "count":
                    value = len(df)
                elif aggregate_func == "min":
                    value = df[aggregate_column].min()
                elif aggregate_func == "max":
                    value = df[aggregate_column].max()
                else:
                    value = df[aggregate_column].sum()
                
                return [{"result": value}]
            
            return rows
            
        except Exception as exc:
            LOGGER.error(f"Aggregation failed: {exc}")
            return []


# =============================================================================
# Singleton Pattern
# =============================================================================

_DATASET_SERVICE: Optional[DatasetService] = None


def get_dataset_service() -> DatasetService:
    """Get or create singleton DatasetService instance."""
    global _DATASET_SERVICE
    if _DATASET_SERVICE is None:
        _DATASET_SERVICE = DatasetService()
    return _DATASET_SERVICE
