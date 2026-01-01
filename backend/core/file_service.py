"""File storage service using local filesystem."""

from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

from core.database import get_db_session
from core.models import StoredFile

logger = logging.getLogger(__name__)

# Default uploads directory
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


class FileService:
    """Service for storing and retrieving files on local filesystem."""
    
    def __init__(self, uploads_dir: Optional[Path] = None):
        self.uploads_dir = uploads_dir or UPLOADS_DIR
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileService initialized with uploads dir: {self.uploads_dir}")
    
    def save_file(
        self,
        filename: str,
        content: bytes,
        session_id: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Save a file to the filesystem.
        
        Args:
            filename: Original filename
            content: File content as bytes
            session_id: Optional session to associate file with
            content_type: Optional MIME type
            metadata: Optional additional metadata
        
        Returns:
            File ID (UUID)
        """
        file_id = uuid4().hex
        
        # Create directory structure: uploads/{session_id or 'general'}/
        if session_id:
            file_dir = self.uploads_dir / session_id
        else:
            file_dir = self.uploads_dir / "general"
        
        file_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename
        safe_filename = self._sanitize_filename(filename)
        filepath = file_dir / f"{file_id}_{safe_filename}"
        
        try:
            # Write file to disk
            with open(filepath, "wb") as f:
                f.write(content)
            
            logger.info(f"File saved: {filename} (ID: {file_id}, size: {len(content)} bytes)")
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise
    
    def get_file(self, file_id: str) -> bytes:
        """
        Retrieve file content by ID.
        
        Args:
            file_id: File identifier
        
        Returns:
            File content as bytes
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        with get_db_session() as db:
            stored_file = db.query(StoredFile).filter(StoredFile.id == file_id).first()
            
            if not stored_file:
                raise FileNotFoundError(f"File not found: {file_id}")
            
            filepath = self.uploads_dir / stored_file.filepath
            
            if not filepath.exists():
                raise FileNotFoundError(f"File missing from disk: {file_id}")
            
            with open(filepath, "rb") as f:
                content = f.read()
            
            logger.info(f"File retrieved: {file_id}")
            return content
    
    def get_file_stream(self, file_id: str) -> BytesIO:
        """
        Get file as BytesIO stream.
        
        Args:
            file_id: File identifier
        
        Returns:
            BytesIO stream of file content
        """
        content = self.get_file(file_id)
        return BytesIO(content)
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from filesystem and database.
        
        Args:
            file_id: File identifier
        
        Returns:
            True if successful
        """
        try:
            with get_db_session() as db:
                stored_file = db.query(StoredFile).filter(StoredFile.id == file_id).first()
                
                if not stored_file:
                    return False
                
                # Delete from filesystem
                filepath = self.uploads_dir / stored_file.filepath
                if filepath.exists():
                    filepath.unlink()
                
                # Delete from database
                db.delete(stored_file)
            
            logger.info(f"File deleted: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def file_exists(self, file_id: str) -> bool:
        """Check if a file exists."""
        with get_db_session() as db:
            stored_file = db.query(StoredFile).filter(StoredFile.id == file_id).first()
            if not stored_file:
                return False
            
            filepath = self.uploads_dir / stored_file.filepath
            return filepath.exists()
    
    def get_file_info(self, file_id: str) -> Optional[dict]:
        """Get metadata about a file."""
        with get_db_session() as db:
            stored_file = db.query(StoredFile).filter(StoredFile.id == file_id).first()
            if not stored_file:
                return None
            return stored_file.to_dict()
    
    def delete_session_files(self, session_id: str) -> int:
        """
        Delete all files associated with a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Number of files deleted
        """
        try:
            with get_db_session() as db:
                files = db.query(StoredFile).filter(StoredFile.session_id == session_id).all()
                count = 0
                
                for stored_file in files:
                    filepath = self.uploads_dir / stored_file.filepath
                    if filepath.exists():
                        filepath.unlink()
                    db.delete(stored_file)
                    count += 1
            
            # Also remove session directory if empty
            session_dir = self.uploads_dir / session_id
            if session_dir.exists() and not any(session_dir.iterdir()):
                session_dir.rmdir()
            
            logger.info(f"Deleted {count} files for session: {session_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to delete session files: {e}")
            return 0
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path separators and null bytes
        safe = filename.replace("/", "_").replace("\\", "_").replace("\x00", "")
        # Limit length
        if len(safe) > 200:
            name, ext = os.path.splitext(safe)
            safe = name[:200-len(ext)] + ext
        return safe or "unnamed"


# Singleton instance
_file_service: Optional[FileService] = None


def get_file_service() -> FileService:
    """Get or create the FileService singleton."""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service
