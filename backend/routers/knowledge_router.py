"""FastAPI router for Knowledge Agent operations."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.knowledge_service import get_shared_service
from shared.utils import clean_response

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
service = get_shared_service()


class KnowledgeAnalyseRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Dataset records")
    generate_insights: bool = Field(default=True)
    generate_recommendations: bool = Field(default=True)


class AskQuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language question about the dataset")


@router.post("/analyze")
def analyze_dataset(payload: KnowledgeAnalyseRequest):
    result = service.analyse(
        data=payload.data,
        generate_insights=payload.generate_insights,
        generate_recommendations=payload.generate_recommendations,
    )
    return clean_response(result)


@router.post("/ask")
def ask_question(payload: AskQuestionRequest):
    result = service.ask(question=payload.question)
    if not result.get("success", True):
        raise HTTPException(status_code=400, detail=result.get("error") or "Unable to answer question")
    return clean_response(result)


class VisualQueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question that may benefit from a chart")
    request_chart: bool = Field(default=True, description="Whether to generate a chart if applicable")


@router.post("/ask-visual")
def ask_visual_question(payload: VisualQueryRequest):
    """
    Answer questions with optional chart generation for visual insights.
    Returns both text answer and chart (if applicable).
    """
    result = service.ask_visual(question=payload.question, generate_chart=payload.request_chart)
    if not result.get("success", True):
        raise HTTPException(status_code=400, detail=result.get("error") or "Unable to answer question")
    return clean_response(result)


@router.get("/summary")
def get_summary():
    return clean_response(service.summary())
