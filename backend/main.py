"""DataCue API - Simplified AI Analytics Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    chat_router,
    dashboard_router,
    ingestion_router,
    otp_router,
)
from core.config import get_settings
from shared.config import get_config

# Load settings
settings = get_settings()

app = FastAPI(
    title="DataCue API",
    description="AI-powered analytics platform with file ingestion, dashboard generation, and chat with data.",
    version="3.0.0",
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
app.include_router(otp_router.router)


@app.get("/")
def root():
    config = get_config()
    return {
        "status": "ok",
        "version": "3.0.0",
        "agents": ["ingestion", "dashboard", "chat"],
        "integrations": {
            "mongo": config.has_mongo,
            "groq": config.has_groq,
        },
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint that verifies MongoDB and other critical services.
    Returns detailed status for frontend to display warnings.
    """
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    
    config = get_config()
    health_status = {
        "status": "healthy",
        "services": {
            "api": "ok",
            "mongodb": "unknown",
            "groq": "ok" if config.has_groq else "not_configured",
        }
    }
    
    # Check MongoDB connection
    if config.has_mongo:
        try:
            client = MongoClient(
                config.mongo_uri,
                serverSelectionTimeoutMS=3000,  # 3 second timeout
                connectTimeoutMS=3000
            )
            # Ping the database to verify connection
            client.admin.command('ping')
            health_status["services"]["mongodb"] = "ok"
            client.close()
        except PyMongoError as e:
            health_status["status"] = "degraded"
            health_status["services"]["mongodb"] = "unreachable"
            health_status["mongodb_error"] = str(e)
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["services"]["mongodb"] = "error"
            health_status["mongodb_error"] = str(e)
    else:
        health_status["services"]["mongodb"] = "not_configured"
    
    return health_status
