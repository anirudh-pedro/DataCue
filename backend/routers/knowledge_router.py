"""FastAPI router for Knowledge Agent operations."""

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
