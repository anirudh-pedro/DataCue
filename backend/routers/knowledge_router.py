"""FastAPI router for Knowledge Agent operations."""

import warnings
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.knowledge_service import get_shared_service
from shared.utils import clean_response

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
service = get_shared_service()


class KnowledgeAnalyseRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(default=None, description="Dataset records (optional if gridfs_id provided)")
    gridfs_id: str = Field(default=None, description="GridFS file ID of the dataset (optional if data provided)")
    generate_insights: bool = Field(default=True)
    generate_recommendations: bool = Field(default=True)
    session_id: str = Field(..., description="Chat session identifier (required)")


class AskQuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language question about the dataset")
    session_id: str = Field(..., description="Chat session identifier (required)")


@router.post("/analyze")
def analyze_dataset(payload: KnowledgeAnalyseRequest):
    try:
        result = service.analyse(
            data=payload.data,
            gridfs_id=payload.gridfs_id,
            generate_insights=payload.generate_insights,
            generate_recommendations=payload.generate_recommendations,
            session_id=payload.session_id,
        )
        return clean_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ask")
def ask_question(payload: AskQuestionRequest):
    try:
        result = service.ask(question=payload.question, session_id=payload.session_id)
        if not result.get("success", True):
            raise HTTPException(status_code=400, detail=result.get("error") or "Unable to answer question")
        return clean_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class VisualQueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question that may benefit from a chart")
    request_chart: bool = Field(default=True, description="Whether to generate a chart if applicable")
    session_id: str = Field(..., description="Chat session identifier (required)")


@router.post("/ask-visual")
def ask_visual_question(payload: VisualQueryRequest):
    """
    Answer questions with optional chart generation for visual insights.
    Returns both text answer and chart (if applicable).
    """
    try:
        result = service.ask_visual(
            question=payload.question,
            session_id=payload.session_id,
            generate_chart=payload.request_chart,
        )
        if not result.get("success", True):
            raise HTTPException(status_code=400, detail=result.get("error") or "Unable to answer question")
        return clean_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary")
def get_summary(session_id: str):
    """Get analysis summary for a specific session."""
    try:
        return clean_response(service.summary(session_id=session_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class AskMongoRequest(BaseModel):
    question: str = Field(..., description="Natural language question to translate into MongoDB query")
    session_id: str = Field(..., description="Session ID with stored dataset")


@router.post("/ask-mongo", deprecated=True)
def ask_mongo_question(payload: AskMongoRequest):
    """
    [DEPRECATED] Use /ask-visual instead for better results.
    
    This endpoint is deprecated and will be removed in a future version.
    The /ask-visual endpoint provides superior results with chart generation.
    """
    warnings.warn(
        "The /ask-mongo endpoint is deprecated. Use /ask-visual instead.",
        DeprecationWarning
    )
    
    # Redirect to the unified ask-visual endpoint
    try:
        result = service.ask_visual(
            question=payload.question,
            session_id=payload.session_id,
            generate_chart=False,  # Maintain backward compatibility - no chart
        )
        if not result.get("success", True):
            raise HTTPException(status_code=400, detail=result.get("error") or "Unable to answer question")
        
        # Format response to match old ask-mongo structure for backward compatibility
        return clean_response({
            "success": True,
            "answer": result.get("answer", ""),
            "query_type": "knowledge_agent",
            "deprecated_notice": "This endpoint is deprecated. Please use /ask-visual instead."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
