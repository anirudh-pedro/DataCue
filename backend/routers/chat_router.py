"""Chat history API router."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from core.auth import FirebaseUser, get_current_user
from core.config import get_settings
from services.chat_service import ChatService, get_chat_service
from services.chat_query_service import ChatQueryService, get_chat_query_service
from services.dataset_service import DatasetService

router = APIRouter(prefix="/chat", tags=["chat"])
dataset_service = DatasetService()


class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., description="Firebase UID for the authenticated user")
    email: Optional[EmailStr] = Field(default=None)
    display_name: Optional[str] = Field(default=None)


class CreateSessionResponse(BaseModel):
    session_id: str


class UpdateTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


class ChatMessagePayload(BaseModel):
    role: str
    content: Optional[str] = None
    timestamp: Optional[str] = None
    chart: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    showDashboardButton: bool = False
    id: Optional[str] = None


class ChatMessagesResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]


class DashboardDataPayload(BaseModel):
    charts: List[Dict[str, Any]]
    dataset_name: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    quality_indicators: Optional[Dict[str, Any]] = None
    metadata_summary: Optional[Dict[str, Any]] = None
    layout: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None


class AskQuestionRequest(BaseModel):
    """Request model for asking questions about data"""
    question: str = Field(..., description="Natural language question about the data")
    session_id: Optional[str] = Field(default=None, description="Session ID for MongoDB data")
    dataset_id: Optional[str] = Field(default=None, description="Dataset ID")
    gridfs_id: Optional[str] = Field(default=None, description="GridFS file ID")
    data: Optional[List[Dict[str, Any]]] = Field(default=None, description="Direct data records")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Column metadata")


def _serialise_message(message: Dict[str, Any]) -> Dict[str, Any]:
    serialised = dict(message)
    created_at: Optional[datetime] = serialised.get("created_at")
    if isinstance(created_at, datetime):
        serialised["created_at"] = created_at.isoformat()
    return serialised


def _validate_session_ownership(
    session: Dict[str, Any],
    user: FirebaseUser,
) -> None:
    """Validate that the session belongs to the authenticated user."""
    settings = get_settings()
    # Skip ownership check in dev mode
    if settings.disable_firebase_auth:
        return
    if session.get("user_id") != user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session"
        )


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(
    payload: CreateSessionRequest,
    current_user: FirebaseUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> CreateSessionResponse:
    settings = get_settings()
    # In dev mode, use the payload's user_id; in production, use authenticated user's ID
    user_id = payload.user_id if settings.disable_firebase_auth else current_user.uid
    email = payload.email if settings.disable_firebase_auth else current_user.email
    
    session = service.create_session(
        user_id=user_id,
        email=email,
        display_name=current_user.name or payload.display_name,
    )
    return CreateSessionResponse(session_id=session["id"])


@router.get("/sessions/{session_id}/messages", response_model=ChatMessagesResponse)
def get_messages(
    session_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatMessagesResponse:
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    _validate_session_ownership(session, current_user)

    messages = [
        _serialise_message(message)
        for message in service.list_messages(session_id)
    ]
    return ChatMessagesResponse(session_id=session_id, messages=messages)


@router.post("/sessions/{session_id}/messages", status_code=status.HTTP_201_CREATED)
def append_message(
    session_id: str,
    payload: ChatMessagePayload,
    current_user: FirebaseUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> Dict[str, Any]:
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    _validate_session_ownership(session, current_user)

    message = service.append_message(
        session_id=session_id,
        user_id=current_user.uid,
        payload=payload.dict(),
    )
    return _serialise_message(message)


@router.post("/sessions/{session_id}/dashboard", status_code=status.HTTP_201_CREATED)
def store_dashboard(
    session_id: str,
    payload: DashboardDataPayload,
    current_user: FirebaseUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> Dict[str, str]:
    """Store dashboard data for a session (canonical source)."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    _validate_session_ownership(session, current_user)
    
    service.store_dashboard_data(session_id, payload.dict())
    return {"status": "stored", "session_id": session_id}


@router.get("/sessions/{session_id}/dashboard")
def get_dashboard(
    session_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> Dict[str, Any]:
    """Retrieve dashboard data for a session from MongoDB."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    _validate_session_ownership(session, current_user)
    
    dashboard_data = service.get_dashboard_data(session_id)
    if not dashboard_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No dashboard data found for this session")
    
    return dashboard_data


@router.patch("/sessions/{session_id}/title")
def update_session_title(
    session_id: str,
    payload: UpdateTitleRequest,
    current_user: FirebaseUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> Dict[str, Any]:
    """Update the title of a chat session."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    _validate_session_ownership(session, current_user)
    
    service.update_session_title(session_id, payload.title)
    return {"session_id": session_id, "title": payload.title}


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_session(
    session_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """Delete a chat session and all its messages."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    _validate_session_ownership(session, current_user)
    
    service.delete_session(session_id)
    return None


@router.get("/sessions/user/{user_id}")
def list_user_sessions(
    user_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> Dict[str, Any]:
    """List all chat sessions for a specific user."""
    settings = get_settings()
    # Skip ownership check in dev mode
    if not settings.disable_firebase_auth and user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own sessions"
        )
    
    sessions = service.list_user_sessions(user_id)
    return {"user_id": user_id, "sessions": sessions}


# ============== CHAT WITH DATA ENDPOINT ==============

@router.post("/ask")
def ask_question(
    payload: AskQuestionRequest,
    current_user: FirebaseUser = Depends(get_current_user),
    query_service: ChatQueryService = Depends(get_chat_query_service),
) -> Dict[str, Any]:
    """
    Ask a natural language question about the dataset.
    
    The question is converted to a safe read-only query using LLM,
    validated, and executed. Returns the result with optional insight.
    
    Example questions:
    - "What is the average revenue by region?"
    - "Show me the top 10 products by sales"
    - "What's the trend of orders over time?"
    """
    try:
        # Verify user owns the dataset if session_id is provided
        if payload.session_id:
            ownership = dataset_service.verify_ownership(
                session_id=payload.session_id,
                user_id=current_user.uid,
                dataset_id=payload.dataset_id
            )
            if not ownership["authorized"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ownership.get("reason", "Access denied to this dataset")
                )
        
        result = query_service.ask(
            question=payload.question,
            session_id=payload.session_id,
            dataset_id=payload.dataset_id,
            gridfs_id=payload.gridfs_id,
            data=payload.data,
            metadata=payload.metadata
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
