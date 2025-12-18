"""Application configuration utilities.

Loads environment variables from `.env` and exposes strongly-typed helpers.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load the .env file located at the project root (next to this module's parent directory).
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)


class Settings:
    """Centralised access to runtime configuration."""

    # API Keys
    groq_api_key: Optional[str]
    mongo_uri: Optional[str]
    
    # LLM Configuration
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int
    
    # Query Engine Limits
    max_numeric_columns_context: int
    max_categorical_columns_context: int
    max_unique_values_display: int
    max_sample_rows: int
    default_top_n: int  # Default for "top N" queries when N not specified
    max_temporal_periods: int  # Max periods shown in temporal queries
    include_sample_data: bool  # Whether to include sample rows in LLM context
    max_full_dataset_rows: int  # Max rows to send full dataset to LLM
    
    # Dashboard Configuration  
    max_charts_per_dashboard: int
    max_kpi_cards: int
    max_insights_display: int
    default_chart_limit: int
    
    # Data Processing
    outlier_threshold_percentage: float
    correlation_threshold: float
    missing_data_threshold: float
    
    # Server Configuration
    api_host: str
    api_port: int
    cors_origins: list[str]
    
    # Pagination & Limits
    default_page_size: int
    max_page_size: int
    cache_ttl_seconds: int
    
    # Firebase Authentication
    disable_firebase_auth: bool
    firebase_project_id: Optional[str]

    def __init__(self) -> None:
        # API Keys
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.mongo_uri = os.getenv("MONGO_URI")
        
        # LLM Configuration
        self.llm_model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "500"))
        
        # Query Engine Limits
        self.max_numeric_columns_context = int(os.getenv("MAX_NUMERIC_COLUMNS_CONTEXT", "5"))
        self.max_categorical_columns_context = int(os.getenv("MAX_CATEGORICAL_COLUMNS_CONTEXT", "5"))
        self.max_unique_values_display = int(os.getenv("MAX_UNIQUE_VALUES_DISPLAY", "10"))
        self.max_sample_rows = int(os.getenv("MAX_SAMPLE_ROWS", "5"))
        self.default_top_n = int(os.getenv("DEFAULT_TOP_N", "5"))
        self.max_temporal_periods = int(os.getenv("MAX_TEMPORAL_PERIODS", "12"))
        self.include_sample_data = os.getenv("INCLUDE_SAMPLE_DATA", "false").lower() == "true"
        self.max_full_dataset_rows = int(os.getenv("MAX_FULL_DATASET_ROWS", "50"))
        
        # Dashboard Configuration
        self.max_charts_per_dashboard = int(os.getenv("MAX_CHARTS_PER_DASHBOARD", "20"))
        self.max_kpi_cards = int(os.getenv("MAX_KPI_CARDS", "4"))
        self.max_insights_display = int(os.getenv("MAX_INSIGHTS_DISPLAY", "10"))
        self.default_chart_limit = int(os.getenv("DEFAULT_CHART_LIMIT", "5"))
        
        # Data Processing
        self.outlier_threshold_percentage = float(os.getenv("OUTLIER_THRESHOLD_PERCENTAGE", "5.0"))
        self.correlation_threshold = float(os.getenv("CORRELATION_THRESHOLD", "0.7"))
        self.missing_data_threshold = float(os.getenv("MISSING_DATA_THRESHOLD", "10.0"))
        
        # Server Configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        cors_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        self.cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
        
        # Pagination & Limits
        self.default_page_size = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
        self.max_page_size = int(os.getenv("MAX_PAGE_SIZE", "100"))
        self.cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        
        # Firebase Authentication
        self.disable_firebase_auth = os.getenv("DISABLE_FIREBASE_AUTH", "false").lower() == "true"
        self.firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", "datacue-50971")

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_mongo(self) -> bool:
        return bool(self.mongo_uri)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
