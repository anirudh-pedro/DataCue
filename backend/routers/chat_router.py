"""Chat history API router."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from services.chat_service import ChatService, get_chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., description="Firebase UID for the authenticated user")
    email: Optional[EmailStr] = Field(default=None)
    display_name: Optional[str] = Field(default=None)


class CreateSessionResponse(BaseModel):
    session_id: str


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


def _serialise_message(message: Dict[str, Any]) -> Dict[str, Any]:
    serialised = dict(message)
    created_at: Optional[datetime] = serialised.get("created_at")
    if isinstance(created_at, datetime):
        serialised["created_at"] = created_at.isoformat()
    return serialised


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(
    payload: CreateSessionRequest,
    service: ChatService = Depends(get_chat_service),
) -> CreateSessionResponse:
    session = service.create_session(
        user_id=payload.user_id,
        email=str(payload.email) if payload.email else None,
        display_name=payload.display_name,
    )
    return CreateSessionResponse(session_id=session["id"])


@router.get("/sessions/{session_id}/messages", response_model=ChatMessagesResponse)
def get_messages(
    session_id: str,
    service: ChatService = Depends(get_chat_service),
) -> ChatMessagesResponse:
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    messages = [
        _serialise_message(message)
        for message in service.list_messages(session_id)
    ]
    return ChatMessagesResponse(session_id=session_id, messages=messages)


@router.post("/sessions/{session_id}/messages", status_code=status.HTTP_201_CREATED)
def append_message(
    session_id: str,
    payload: ChatMessagePayload,
    service: ChatService = Depends(get_chat_service),
) -> Dict[str, Any]:
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    message = service.append_message(
        session_id=session_id,
        user_id=session["user_id"],
        payload=payload.dict(),
    )
    return _serialise_message(message)


@router.post("/sessions/{session_id}/dashboard", status_code=status.HTTP_201_CREATED)
def store_dashboard(
    session_id: str,
    payload: DashboardDataPayload,
    service: ChatService = Depends(get_chat_service),
) -> Dict[str, str]:
    """Store dashboard data for a session (canonical source)."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    service.store_dashboard_data(session_id, payload.dict())
    return {"status": "stored", "session_id": session_id}


@router.get("/sessions/{session_id}/dashboard")
def get_dashboard(
    session_id: str,
    service: ChatService = Depends(get_chat_service),
) -> Dict[str, Any]:
    """Retrieve dashboard data for a session from MongoDB."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    dashboard_data = service.get_dashboard_data(session_id)
    if not dashboard_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No dashboard data found for this session")
    
    return dashboard_data


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    service: ChatService = Depends(get_chat_service),
) -> None:
    """Delete a chat session and all its messages."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    service.delete_session(session_id)


@router.get("/sessions/user/{user_id}")
def list_user_sessions(
    user_id: str,
    service: ChatService = Depends(get_chat_service),
) -> Dict[str, Any]:
    """List all chat sessions for a specific user."""
    sessions = service.list_user_sessions(user_id)
    return {"user_id": user_id, "sessions": sessions}
