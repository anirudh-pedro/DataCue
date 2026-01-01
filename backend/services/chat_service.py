"""Chat persistence service with PostgreSQL backing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.database import get_db_session
from core.models import ChatSession, ChatMessage

_LOGGER = logging.getLogger(__name__)

# Maximum messages per session (to prevent unbounded growth)
MAX_MESSAGES_PER_SESSION = 100


class ChatService:
    """Facade handling chat persistence with PostgreSQL."""

    def __init__(self) -> None:
        _LOGGER.info("ChatService initialized with PostgreSQL")

    # =========================================================================
    # Session Management
    # =========================================================================
    
    def create_session(
        self, 
        user_id: str, 
        email: Optional[str] = None, 
        display_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new chat session."""
        with get_db_session() as db:
            session = ChatSession(
                user_id=user_id,
                email=email,
                display_name=display_name,
            )
            db.add(session)
            db.flush()  # Get ID before commit
            
            result = session.to_dict()
            _LOGGER.info(f"Created chat session: {session.id}")
            return result

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID."""
        with get_db_session() as db:
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            
            if not session:
                return None
            
            return session.to_dict()

    def update_session_title(self, session_id: str, title: str) -> None:
        """Update the title of a chat session."""
        with get_db_session() as db:
            db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).update({
                "title": title,
                "updated_at": datetime.now(timezone.utc),
            })
            _LOGGER.info(f"Updated session title: {session_id}")

    def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages (cascade)."""
        with get_db_session() as db:
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            
            if session:
                db.delete(session)
                _LOGGER.info(f"Deleted session: {session_id}")

    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all sessions for a specific user."""
        with get_db_session() as db:
            sessions = db.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).order_by(desc(ChatSession.updated_at)).all()
            
            result = []
            for session in sessions:
                # Count messages
                message_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session.id
                ).count()
                
                session_dict = session.to_dict()
                session_dict["session_id"] = session.id  # Alias for compatibility
                session_dict["message_count"] = message_count
                session_dict["has_dashboard"] = session.dashboard_data is not None
                result.append(session_dict)
            
            return result

    # =========================================================================
    # Message Management
    # =========================================================================
    
    def list_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        with get_db_session() as db:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at).all()
            
            return [msg.to_dict() for msg in messages]

    def append_message(
        self, 
        session_id: str, 
        user_id: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Append a message to a session."""
        with get_db_session() as db:
            # Check message count and enforce limit
            current_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).count()
            
            if current_count >= MAX_MESSAGES_PER_SESSION:
                # Delete oldest messages to make room
                oldest = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(ChatMessage.created_at).limit(10).all()
                
                for msg in oldest:
                    db.delete(msg)
                
                _LOGGER.info(f"Pruned {len(oldest)} old messages from session {session_id}")
            
            # Normalize ID - strip dashes from UUID to fit in 32 chars
            msg_id = payload.get("id")
            if msg_id:
                msg_id = msg_id.replace("-", "")[:32]
            
            # Create new message
            message = ChatMessage(
                id=msg_id,
                session_id=session_id,
                user_id=user_id,
                role=payload.get("role", "assistant"),
                content=payload.get("content"),
                timestamp=payload.get("timestamp"),
                chart=payload.get("chart"),
                metadata_=payload.get("metadata") or {},
                show_dashboard_button=bool(payload.get("showDashboardButton")),
            )
            db.add(message)
            
            # Update session timestamp
            db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).update({"updated_at": datetime.now(timezone.utc)})
            
            db.flush()
            result = message.to_dict()
            
            return result

    # =========================================================================
    # Dashboard Data Management
    # =========================================================================
    
    def store_dashboard_data(self, session_id: str, dashboard_data: Dict[str, Any]) -> None:
        """Store dashboard data for a session."""
        with get_db_session() as db:
            db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).update({
                "dashboard_data": dashboard_data,
                "updated_at": datetime.now(timezone.utc),
            })
            _LOGGER.info(f"Stored dashboard data for session: {session_id}")

    def get_dashboard_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve dashboard data for a session."""
        with get_db_session() as db:
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            
            if not session:
                return None
            
            return session.dashboard_data


# =============================================================================
# Singleton Pattern
# =============================================================================

_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get or create singleton ChatService instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


def reset_chat_service() -> None:
    """Reset the chat service singleton (for testing)."""
    global _chat_service
    _chat_service = None
