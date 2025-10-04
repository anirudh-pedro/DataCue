"""
Knowledge Agent - Phase 4
Data Understanding & Insights Agent

This agent transforms cleaned datasets into human-like insights by:
- Profiling data and discovering patterns
- Extracting insights using LLM + Statistics fusion
- Answering natural language questions about data
- Recommending next analytical steps
- Generating comprehensive EDA reports

New Features (v1.1.0):
- Conversation memory and context awareness
- AI confidence scoring for insights
- Interactive Plotly visualizations

Enhanced Features (v1.2.0):
- User feedback system for insights
- Advanced anomaly detection with alerts
- PNG/PDF/SVG export for visualizations
"""

from .knowledge_agent import KnowledgeAgent
from .data_profiler import DataProfiler
from .insight_generator import InsightGenerator
from .query_engine import QueryEngine
from .recommendation_engine import RecommendationEngine
from .report_generator import ReportGenerator

# New features (v1.1.0)
from .conversation_manager import ConversationManager
from .confidence_scorer import ConfidenceScorer, ConfidenceLevel
from .visualization_generator import VisualizationGenerator

# Enhanced features (v1.2.0)
from .feedback_system import FeedbackSystem
from .anomaly_detector import AnomalyDetector, AlertSeverity

__all__ = [
    'KnowledgeAgent',
    'DataProfiler',
    'InsightGenerator',
    'QueryEngine',
    'RecommendationEngine',
    'ReportGenerator',
    'ConversationManager',
    'ConfidenceScorer',
    'ConfidenceLevel',
    'VisualizationGenerator',
    'FeedbackSystem',
    'AnomalyDetector',
    'AlertSeverity'
]

__version__ = '1.2.0'
__author__ = 'DataCue Team'
