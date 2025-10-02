"""
File Ingestion Agent Module
Handles file upload processing, data cleaning, and metadata extraction
"""

from .ingestion_agent import FileIngestionAgent
from .data_cleaner import DataCleaner
from .metadata_extractor import MetadataExtractor

__all__ = ["FileIngestionAgent", "DataCleaner", "MetadataExtractor"]
