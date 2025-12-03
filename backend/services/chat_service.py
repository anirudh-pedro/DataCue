"""Chat persistence service with MongoDB backing and in-memory fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from shared.config import get_config

_LOGGER = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Representation of a stored chat message."""

    id: str
    session_id: str
    user_id: str
    role: str
    content: Optional[str]
    timestamp: Optional[str]
    chart: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    show_dashboard_button: bool
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "chart": self.chart,
            "metadata": self.metadata,
            "showDashboardButton": self.show_dashboard_button,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_payload(session_id: str, user_id: str, payload: Dict[str, Any]) -> "ChatMessage":
        return ChatMessage(
            id=payload.get("id") or uuid4().hex,
            session_id=session_id,
            user_id=user_id,
            role=payload.get("role", "assistant"),
            content=payload.get("content"),
            timestamp=payload.get("timestamp"),
            chart=payload.get("chart"),
            metadata=payload.get("metadata") or {},
            show_dashboard_button=bool(payload.get("showDashboardButton")),
            created_at=datetime.now(timezone.utc),
        )


class _InMemoryChatStore:
    """Simple in-memory chat persistence used when MongoDB is unavailable."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.messages: Dict[str, List[Dict[str, Any]]] = {}
        self.dashboards: Dict[str, Dict[str, Any]] = {}  # Store dashboard data

    def create_session(self, user_id: str, email: Optional[str], display_name: Optional[str]) -> Dict[str, Any]:
        session_id = uuid4().hex
        session = {
            "id": session_id,
            "user_id": user_id,
            "email": email,
            "display_name": display_name,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.sessions[session_id] = session
        self.messages.setdefault(session_id, [])
        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)

    def list_messages(self, session_id: str) -> List[Dict[str, Any]]:
        return list(self.messages.get(session_id, []))

    def append_message(self, message: ChatMessage) -> None:
        self.messages.setdefault(message.session_id, []).append(
            {**message.to_dict(), "created_at": message.created_at}
        )
        if message.session_id in self.sessions:
            self.sessions[message.session_id]["updated_at"] = message.created_at

    def store_dashboard_data(self, session_id: str, dashboard_data: Dict[str, Any]) -> None:
        """Store dashboard data for a session."""
        self.dashboards[session_id] = dashboard_data

    def get_dashboard_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve dashboard data for a session."""
        return self.dashboards.get(session_id)

    def update_session_title(self, session_id: str, title: str) -> None:
        """Update the title of a session."""
        if session_id in self.sessions:
            self.sessions[session_id]["title"] = title
            self.sessions[session_id]["updated_at"] = datetime.utcnow()

    def delete_session(self, session_id: str) -> None:
        """Delete a session and its messages."""
        self.sessions.pop(session_id, None)
        self.messages.pop(session_id, None)
        self.dashboards.pop(session_id, None)

    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all sessions for a user."""
        return [
            session for session in self.sessions.values()
            if session.get("user_id") == user_id
        ]


class ChatService:
    """Facade handling chat persistence with optional MongoDB backing."""

    def __init__(self) -> None:
        self._config = get_config()
        self._client: Optional[MongoClient] = None
        self._sessions: Optional[Collection] = None
        self._messages: Optional[Collection] = None
        self._fallback = _InMemoryChatStore()

        if self._config.has_mongo and self._config.mongo_uri:
            try:
                self._client = MongoClient(self._config.mongo_uri, serverSelectionTimeoutMS=2_000)
                # Trigger connection test
                self._client.admin.command("ping")
                db = self._client.get_default_database()
                if db is None:
                    db = self._client["datacue"]
                self._sessions = db["chat_sessions"]
                self._messages = db["chat_messages"]
                
                # Create indexes for performance
                self._sessions.create_index([("user_id", ASCENDING)])
                self._messages.create_index([("session_id", ASCENDING), ("created_at", ASCENDING)])
                
                # Create TTL index to auto-expire sessions after 30 days of inactivity
                # MongoDB will automatically delete documents where updated_at is older than 30 days
                self._sessions.create_index(
                    [("updated_at", ASCENDING)],
                    expireAfterSeconds=2592000  # 30 days in seconds (30 * 24 * 60 * 60)
                )
                
                _LOGGER.info("ChatService connected to MongoDB with TTL index on sessions")
            except PyMongoError as exc:
                _LOGGER.warning("ChatService falling back to in-memory store: %s", exc)
                self._client = None
                self._sessions = None
                self._messages = None
        else:
            _LOGGER.info("ChatService using in-memory store (MongoDB disabled)")

    # Session management -------------------------------------------------
    def create_session(self, user_id: str, email: Optional[str], display_name: Optional[str]) -> Dict[str, Any]:
        if self._sessions is None:
            return self._fallback.create_session(user_id, email, display_name)

        session_id = uuid4().hex
        document = {
            "_id": session_id,
            "user_id": user_id,
            "email": email,
            "display_name": display_name,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self._sessions.insert_one(document)
        return {
            "id": session_id,
            "user_id": user_id,
            "email": email,
            "display_name": display_name,
            "created_at": document["created_at"],
            "updated_at": document["updated_at"],
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self._sessions is None:
            return self._fallback.get_session(session_id)
        document = self._sessions.find_one({"_id": session_id})
        if not document:
            return None
        return {
            "id": document.get("_id"),
            "user_id": document.get("user_id"),
            "email": document.get("email"),
            "display_name": document.get("display_name"),
            "created_at": document.get("created_at"),
            "updated_at": document.get("updated_at"),
        }

    # Message management -------------------------------------------------
    def list_messages(self, session_id: str) -> List[Dict[str, Any]]:
        if self._messages is None:
            return self._fallback.list_messages(session_id)
        cursor = self._messages.find({"session_id": session_id}).sort("created_at", ASCENDING)
        messages = []
        for document in cursor:
            messages.append({
                "id": document.get("id"),
                "session_id": document.get("session_id"),
                "user_id": document.get("user_id"),
                "role": document.get("role"),
                "content": document.get("content"),
                "timestamp": document.get("timestamp"),
                "chart": document.get("chart"),
                "metadata": document.get("metadata", {}),
                "showDashboardButton": document.get("showDashboardButton", False),
                "created_at": document.get("created_at"),
            })
        return messages

    def append_message(self, session_id: str, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        message = ChatMessage.from_payload(session_id=session_id, user_id=user_id, payload=payload)

        if self._messages is None:
            self._fallback.append_message(message)
        else:
            document = message.to_dict()
            self._messages.insert_one(document)
            self._sessions.update_one(
                {"_id": session_id},
                {"$set": {"updated_at": message.created_at}},
                upsert=False,
            )

        return message.to_dict()

    # Dashboard data management ------------------------------------------
    def store_dashboard_data(self, session_id: str, dashboard_data: Dict[str, Any]) -> None:
        """Store dashboard data for a session in MongoDB (canonical source)."""
        if self._sessions is None:
            self._fallback.store_dashboard_data(session_id, dashboard_data)
        else:
            self._sessions.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "dashboard_data": dashboard_data,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
                upsert=False,
            )

    def get_dashboard_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve dashboard data for a session from MongoDB."""
        if self._sessions is None:
            return self._fallback.get_dashboard_data(session_id)
        
        session = self._sessions.find_one({"_id": session_id})
        if not session:
            return None
        return session.get("dashboard_data")

    # Session management ------------------------------------
    def update_session_title(self, session_id: str, title: str) -> None:
        """Update the title of a chat session."""
        if self._sessions is None:
            self._fallback.update_session_title(session_id, title)
        else:
            self._sessions.update_one(
                {"_id": session_id},
                {"$set": {"title": title, "updated_at": datetime.utcnow()}}
            )

    # Session deletion and listing ------------------------------------
    def delete_session(self, session_id: str) -> None:
        """Delete a session and all its associated messages."""
        if self._sessions is None:
            self._fallback.delete_session(session_id)
        else:
            # Delete session document
            self._sessions.delete_one({"_id": session_id})
            # Delete all associated messages
            if self._messages is not None:
                self._messages.delete_many({"session_id": session_id})

    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all sessions for a specific user."""
        if self._sessions is None:
            return self._fallback.list_user_sessions(user_id)
        
        cursor = self._sessions.find({"user_id": user_id}).sort("updated_at", -1)
        sessions = []
        for doc in cursor:
            # Count messages for this session
            message_count = 0
            if self._messages is not None:
                message_count = self._messages.count_documents({"session_id": doc.get("_id")})
            
            sessions.append({
                "session_id": doc.get("_id"),
                "id": doc.get("_id"),
                "user_id": doc.get("user_id"),
                "email": doc.get("email"),
                "display_name": doc.get("display_name"),
                "title": doc.get("title", "New Chat"),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
                "has_dashboard": bool(doc.get("dashboard_data")),
                "message_count": message_count,
            })
        return sessions


_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


def reset_chat_service() -> None:
    global _chat_service
    _chat_service = None
