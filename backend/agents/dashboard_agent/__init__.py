"""Dashboard Agent - AI-powered dashboard generation"""
from .dashboard_agent import DashboardAgent
from .enhanced_dashboard_agent import EnhancedDashboardAgent
from .structured_prompts import (
    build_dashboard_planner_prompt,
    build_sql_generation_prompt,
    validate_sql_safety,
    extract_json_from_response
)

# Default to enhanced agent (with structural prompts)
# Set USE_ENHANCED_DASHBOARD_AGENT=false in .env to use legacy agent
import os
USE_ENHANCED = os.getenv("USE_ENHANCED_DASHBOARD_AGENT", "true").lower() == "true"

# Export the active agent as DashboardAgent for backward compatibility
if USE_ENHANCED:
    DashboardAgent = EnhancedDashboardAgent

__all__ = [
    "DashboardAgent", 
    "EnhancedDashboardAgent",
    "build_dashboard_planner_prompt",
    "build_sql_generation_prompt",
    "validate_sql_safety",
    "extract_json_from_response"
]
