"""Service layer exposing dashboard generation workflows."""

from typing import Any, Dict

import pandas as pd

from agents.dashboard_generator_agent.dashboard_generator import DashboardGenerator


class DashboardService:
    def __init__(self) -> None:
        self._generator = DashboardGenerator()

    def generate(self, data: Dict[str, Any], metadata: Dict[str, Any], **options: Any) -> Dict[str, Any]:
        dataframe = pd.DataFrame(data)
        return self._generator.generate_dashboard(
            data=dataframe,
            metadata=metadata,
            dashboard_type=options.get("dashboard_type", "auto"),
            include_advanced_charts=options.get("include_advanced_charts", True),
            generate_insights=options.get("generate_insights", True),
        )
