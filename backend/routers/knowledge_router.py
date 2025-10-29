"""FastAPI router for Knowledge Agent operations."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.chat_service import ChatService, get_chat_service
from services.knowledge_service import get_shared_service
from shared.auth import AuthenticatedUser, get_authenticated_user
from shared.utils import clean_response

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
service = get_shared_service()


class KnowledgeAnalyseRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Dataset records")
    generate_insights: bool = Field(default=True)
    generate_recommendations: bool = Field(default=True)
    session_id: str = Field(..., description="Chat session identifier (required)")


class AskQuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language question about the dataset")
    session_id: str = Field(..., description="Chat session identifier (required)")


@router.post("/analyze")
def analyze_dataset(
    payload: KnowledgeAnalyseRequest,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
    chat_store: ChatService = Depends(get_chat_service),
):
    try:
        if payload.session_id:
            session = chat_store.get_session(payload.session_id)
            if not session or session.get("user_id") != current_user.uid:
                raise HTTPException(status_code=404, detail="Chat session not found")
        result = service.analyse(
            data=payload.data,
            generate_insights=payload.generate_insights,
            generate_recommendations=payload.generate_recommendations,
            session_id=payload.session_id,
        )
        return clean_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ask")
def ask_question(
    payload: AskQuestionRequest,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
    chat_store: ChatService = Depends(get_chat_service),
):
    session = chat_store.get_session(payload.session_id)
    if not session or session.get("user_id") != current_user.uid:
        raise HTTPException(status_code=404, detail="Chat session not found")
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
def ask_visual_question(
    payload: VisualQueryRequest,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
    chat_store: ChatService = Depends(get_chat_service),
):
    session = chat_store.get_session(payload.session_id)
    if not session or session.get("user_id") != current_user.uid:
        raise HTTPException(status_code=404, detail="Chat session not found")
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
def get_summary(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
    chat_store: ChatService = Depends(get_chat_service),
):
    """Get analysis summary for a specific session."""
    session = chat_store.get_session(session_id)
    if not session or session.get("user_id") != current_user.uid:
        raise HTTPException(status_code=404, detail="Chat session not found")
    try:
        return clean_response(service.summary(session_id=session_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
