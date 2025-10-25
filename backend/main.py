"""Unified FastAPI application orchestrating all DataCue agents."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    chat_router,
    dashboard_router,
    ingestion_router,
    knowledge_router,
    orchestrator_router,
    otp_router,
    prediction_router,
)
from shared.config import get_config

app = FastAPI(
    title="DataCue Orchestrator",
    description="Single entry point exposing ingestion, dashboard, knowledge, and prediction services.",
    version="2.0.0",
)

# Get allowed origins from environment variable or use defaults
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Default to localhost for development
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router.router)
app.include_router(dashboard_router.router)
app.include_router(knowledge_router.router)
app.include_router(prediction_router.router)
app.include_router(orchestrator_router.router)
app.include_router(chat_router.router)
app.include_router(otp_router.router)


@app.get("/")
def root():
    config = get_config()
    return {
        "status": "ok",
        "agents": ["ingestion", "dashboard", "knowledge", "prediction"],
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
