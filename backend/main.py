"""DataCue API - Simplified AI Analytics Platform."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    chat_router,
    dashboard_router,
    ingestion_router,
    knowledge_router,
    orchestrator_router,
    otp_router,
)
from core.config import get_settings
from core.database import init_database, check_database_connection, close_database
from shared.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Initialize database
    logger.info("Starting DataCue API...")
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown: Close database connections
    logger.info("Shutting down DataCue API...")
    close_database()


app = FastAPI(
    title="DataCue API",
    description="AI-powered analytics platform with file ingestion, dashboard generation, and chat with data.",
    version="3.1.0",  # Updated for PostgreSQL
    lifespan=lifespan,
)

# Use centralized CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core routers only
app.include_router(ingestion_router.router)
app.include_router(dashboard_router.router)
app.include_router(chat_router.router)
app.include_router(knowledge_router.router)
app.include_router(orchestrator_router.router)
app.include_router(otp_router.router)


@app.get("/")
def root():
    """Root endpoint with API status and version info."""
    config = get_config()
    return {
        "status": "ok",
        "version": "3.1.0",
        "agents": ["ingestion", "dashboard", "chat"],
        "integrations": {
            "database": config.has_database,
            "groq": config.has_groq,
        },
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint that verifies PostgreSQL and other critical services.
    Returns detailed status for frontend to display warnings.
    """
    config = get_config()
    
    # Check database connection
    db_status = check_database_connection()
    
    health_status = {
        "status": "healthy" if db_status["status"] == "ok" else "degraded",
        "services": {
            "api": "ok",
            "database": db_status["status"],
            "groq": "ok" if config.has_groq else "not_configured",
        }
    }
    
    if db_status.get("error"):
        health_status["database_error"] = db_status["error"]
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
