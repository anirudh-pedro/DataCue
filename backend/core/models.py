"""SQLAlchemy ORM models for DataCue."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    BigInteger,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


def generate_uuid() -> str:
    """Generate a UUID hex string."""
    return uuid4().hex


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


# =============================================================================
# Chat Models
# =============================================================================

class ChatSession(Base):
    """User chat session."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(128), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    title = Column(String(100), nullable=True, default="New Chat")
    
    # Dashboard data stored as JSON
    dashboard_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_chat_sessions_user_updated", "user_id", "updated_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.email,
            "display_name": self.display_name,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ChatMessage(Base):
    """Message within a chat session."""
    
    __tablename__ = "chat_messages"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    session_id = Column(String(32), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(128), nullable=False)
    
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=True)
    timestamp = Column(String(50), nullable=True)
    
    # Chart data stored as JSON
    chart = Column(JSON, nullable=True)
    
    # Additional metadata
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    show_dashboard_button = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    __table_args__ = (
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "chart": self.chart,
            "metadata": self.metadata_ or {},
            "showDashboardButton": self.show_dashboard_button,
            "created_at": self.created_at,
        }


# =============================================================================
# Dataset Models
# =============================================================================

class Dataset(Base):
    """Dataset metadata."""
    
    __tablename__ = "datasets"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    session_id = Column(String(32), nullable=False, index=True)
    user_id = Column(String(128), nullable=True)
    
    name = Column(String(255), nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    
    # Column information stored as JSON
    # Format: [{"name": "col1", "type": "numeric", ...}, ...]
    columns = Column(JSON, nullable=True)
    column_types = Column(JSON, nullable=True)
    
    # Additional metadata from ingestion
    metadata_ = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    rows = relationship("DatasetRow", back_populates="dataset", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_datasets_session_created", "session_id", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "dataset_name": self.name,
            "row_count": self.row_count,
            "columns": self.columns,
            "column_types": self.column_types,
            "metadata": self.metadata_ or {},
            "created_at": self.created_at,
        }


class DatasetRow(Base):
    """Individual row of dataset data."""
    
    __tablename__ = "dataset_rows"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dataset_id = Column(String(32), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    row_index = Column(Integer, nullable=False)
    
    # Row data stored as JSON object
    # Format: {"column1": value1, "column2": value2, ...}
    data = Column(JSON, nullable=False)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="rows")
    
    __table_args__ = (
        Index("ix_dataset_rows_dataset_id", "dataset_id"),
    )


# =============================================================================
# File Storage Model
# =============================================================================

class StoredFile(Base):
    """Metadata for files stored on filesystem."""
    
    __tablename__ = "stored_files"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    session_id = Column(String(32), nullable=True, index=True)
    
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)  # Relative path from uploads dir
    size_bytes = Column(BigInteger, nullable=False)
    content_type = Column(String(100), nullable=True)
    
    # Additional metadata
    metadata_ = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_id": self.id,
            "session_id": self.session_id,
            "filename": self.filename,
            "filepath": self.filepath,
            "size_bytes": self.size_bytes,
            "content_type": self.content_type,
            "metadata": self.metadata_ or {},
            "created_at": self.created_at,
        }
