"""Service layer exposing dashboard generation workflows."""

import re
from typing import Any, Dict

import pandas as pd

from agents.dashboard_generator_agent.dashboard_generator import DashboardGenerator
from core.gridfs_service import get_gridfs_service


def _standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to match metadata (lowercase, underscores)."""
    new_columns = []
    for col in df.columns:
        col_name = str(col).lower()
        col_name = re.sub(r'[^\w\s]', '', col_name)
        col_name = re.sub(r'\s+', '_', col_name)
        col_name = col_name.strip('_')
        if not col_name:
            col_name = f"column_{len(new_columns)}"
        new_columns.append(col_name)
    
    # Handle duplicates
    seen = {}
    unique_columns = []
    for col in new_columns:
        if col in seen:
            seen[col] += 1
            unique_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            unique_columns.append(col)
    
    df.columns = unique_columns
    return df


class DashboardService:
    def __init__(self) -> None:
        self._generator = DashboardGenerator()

    def generate(
        self, 
        data: Dict[str, Any] = None, 
        gridfs_id: str = None,
        metadata: Dict[str, Any] = None, 
        **options: Any
    ) -> Dict[str, Any]:
        # Load from GridFS if ID provided, otherwise use data
        if gridfs_id:
            gridfs_service = get_gridfs_service()
            file_stream = gridfs_service.get_file_stream(gridfs_id)
            dataframe = pd.read_csv(file_stream)
            # Standardize column names to match metadata
            dataframe = _standardize_column_names(dataframe)
        elif data:
            dataframe = pd.DataFrame(data)
        else:
            raise ValueError("Either 'data' or 'gridfs_id' must be provided")
            
        return self._generator.generate_dashboard(
            data=dataframe,
            metadata=metadata or {},
            dashboard_type=options.get("dashboard_type", "auto"),
            include_advanced_charts=options.get("include_advanced_charts", True),
            generate_insights=options.get("generate_insights", True),
        )
