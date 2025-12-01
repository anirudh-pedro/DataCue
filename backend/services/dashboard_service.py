"""Service layer exposing dashboard generation workflows."""

from typing import Any, Dict

import pandas as pd

from agents.dashboard_generator_agent.dashboard_generator import DashboardGenerator
from core.gridfs_service import get_gridfs_service


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
