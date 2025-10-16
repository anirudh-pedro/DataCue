"""Unified FastAPI application orchestrating all DataCue agents."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    dashboard_router,
    ingestion_router,
    knowledge_router,
    otp_router,
    orchestrator_router,
    prediction_router,
)
from shared.config import get_config

app = FastAPI(
    title="DataCue Orchestrator",
    description="Single entry point exposing ingestion, dashboard, knowledge, and prediction services.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router.router)
app.include_router(dashboard_router.router)
app.include_router(knowledge_router.router)
app.include_router(prediction_router.router)
app.include_router(orchestrator_router.router)
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
    return {"status": "healthy"}
