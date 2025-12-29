"""
Agents Module
Contains all intelligent agents for the DataCue platform

Agents:
- FileIngestionAgent: Parse CSV/Excel, clean data, fix columns with LLM
- DashboardAgent: Generate dashboard configs using LLM
- ChatAgent: Natural language queries on datasets
"""
from .file_ingestion_agent import FileIngestionAgent
from .dashboard_agent import DashboardAgent
from .chat_agent import ChatAgent

__all__ = ["FileIngestionAgent", "DashboardAgent", "ChatAgent"]
