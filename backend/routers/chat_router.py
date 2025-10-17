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
