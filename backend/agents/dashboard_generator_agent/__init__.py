"""
Dashboard Generator Agent
Automatically creates intelligent dashboards from ingested data
Phase 3: Enhanced with AI insights, advanced charts, performance optimization, and export
"""

from .dashboard_generator import DashboardGenerator
from .chart_factory import ChartFactory
from .layout_manager import LayoutManager
from .chart_recommender import ChartRecommendationEngine
from .customization_manager import DashboardCustomizer
from .insight_generator import InsightGenerator
from .performance_optimizer import PerformanceOptimizer
from .dashboard_exporter import DashboardExporter

__all__ = [
    'DashboardGenerator',
    'ChartFactory',
    'LayoutManager',
    'ChartRecommendationEngine',
    'DashboardCustomizer',
    'InsightGenerator',
    'PerformanceOptimizer',
    'DashboardExporter'
]
