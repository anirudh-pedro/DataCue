"""MongoDB GridFS service for file storage."""

from __future__ import annotations

import gridfs
from pymongo import MongoClient
from typing import Optional
import logging
from io import BytesIO

from shared.config import get_config

logger = logging.getLogger(__name__)


class GridFSService:
    """Service for storing and retrieving files using MongoDB GridFS."""
    
    def __init__(self):
        config = get_config()
        if not config.has_mongo:
            raise ValueError("MongoDB connection is required for GridFS storage")
        
        self.client = MongoClient(config.mongo_uri)
        
        # Extract database name from URI or use default 'datacue'
        from urllib.parse import urlparse
        parsed_uri = urlparse(config.mongo_uri)
        db_name = parsed_uri.path.lstrip('/').split('?')[0] if parsed_uri.path and len(parsed_uri.path.lstrip('/')) > 0 else 'datacue'
        
        self.db = self.client[db_name]
        self.fs = gridfs.GridFS(self.db)
        logger.info(f"GridFS service initialized successfully (database: {db_name})")
    
    def save_file(self, filename: str, content: bytes, metadata: Optional[dict] = None) -> str:
        """
        Save a file to GridFS.
        
        Args:
            filename: Name of the file
            content: File content as bytes
            metadata: Optional metadata to store with the file
        
        Returns:
            GridFS file ID as string
        """
        try:
            file_id = self.fs.put(
                content,
                filename=filename,
                metadata=metadata or {}
            )
            logger.info(f"File saved to GridFS: {filename} (ID: {file_id})")
            return str(file_id)
        except Exception as e:
            logger.error(f"Failed to save file to GridFS: {e}")
            raise
    
    def get_file(self, file_id: str) -> bytes:
        """
        Retrieve a file from GridFS.
        
        Args:
            file_id: GridFS file ID
        
        Returns:
            File content as bytes
        """
        try:
            from bson.objectid import ObjectId
            grid_out = self.fs.get(ObjectId(file_id))
            content = grid_out.read()
            logger.info(f"File retrieved from GridFS: {file_id}")
            return content
        except Exception as e:
            logger.error(f"Failed to retrieve file from GridFS: {e}")
            raise
    
    def get_file_stream(self, file_id: str) -> BytesIO:
        """
        Get file as BytesIO stream for pandas/other libraries.
        
        Args:
            file_id: GridFS file ID
        
        Returns:
            BytesIO stream of file content
        """
        content = self.get_file(file_id)
        return BytesIO(content)
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from GridFS.
        
        Args:
            file_id: GridFS file ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from bson.objectid import ObjectId
            self.fs.delete(ObjectId(file_id))
            logger.info(f"File deleted from GridFS: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from GridFS: {e}")
            return False
    
    def file_exists(self, file_id: str) -> bool:
        """
        Check if a file exists in GridFS.
        
        Args:
            file_id: GridFS file ID
        
        Returns:
            True if file exists, False otherwise
        """
        try:
            from bson.objectid import ObjectId
            return self.fs.exists(ObjectId(file_id))
        except Exception:
            return False
    
    def get_file_info(self, file_id: str) -> Optional[dict]:
        """
        Get metadata about a file.
        
        Args:
            file_id: GridFS file ID
        
        Returns:
            Dictionary with file info or None
        """
        try:
            from bson.objectid import ObjectId
            grid_out = self.fs.get(ObjectId(file_id))
            return {
                "file_id": str(grid_out._id),
                "filename": grid_out.filename,
                "length": grid_out.length,
                "upload_date": grid_out.upload_date,
                "metadata": grid_out.metadata
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None


# Singleton instance
_gridfs_service: Optional[GridFSService] = None


def get_gridfs_service() -> GridFSService:
    """Get or create the GridFS service singleton."""
    global _gridfs_service
    if _gridfs_service is None:
        _gridfs_service = GridFSService()
    return _gridfs_service
