"""FastAPI router for dashboard generation."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.auth import get_current_user, FirebaseUser
from services.dashboard_service import DashboardService
from services.dataset_service import DatasetService
from shared.utils import clean_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = DashboardService()
dataset_service = DatasetService()


class GenerateDashboardRequest(BaseModel):
    """Request model for dashboard generation"""
    data: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Dataset records (optional if gridfs_id or session_id provided)"
    )
    gridfs_id: Optional[str] = Field(
        default=None, 
        description="GridFS file ID of the dataset"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for MongoDB data"
    )
    dataset_id: Optional[str] = Field(
        default=None,
        description="Dataset ID in MongoDB"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Column metadata from ingestion"
    )
    user_prompt: Optional[str] = Field(
        default=None,
        description="Optional user guidance for dashboard generation"
    )


@router.post("/generate")
def generate_dashboard(
    payload: GenerateDashboardRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Generate a dashboard from dataset
    
    The LLM analyzes the data schema and suggests appropriate charts.
    Each chart is executed server-side and data is returned.
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
                    status_code=403,
                    detail=ownership.get("reason", "Access denied to this dataset")
                )
        
        result = service.generate(
            data=payload.data,
            gridfs_id=payload.gridfs_id,
            session_id=payload.session_id,
            dataset_id=payload.dataset_id,
            metadata=payload.metadata,
            user_prompt=payload.user_prompt
        )
        return clean_response(result)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health():
    """Health check for dashboard service"""
    return {"status": "ok", "service": "dashboard"}
