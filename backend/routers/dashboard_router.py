"""FastAPI router exposing dashboard generation endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.dashboard_service import DashboardService
from shared.utils import clean_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = DashboardService()


class DashboardRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(default=None, description="Dataset records (optional if gridfs_id provided)")
    gridfs_id: str = Field(default=None, description="GridFS file ID of the dataset (optional if data provided)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata extracted from ingestion agent")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Dashboard generation options")


@router.post("/generate")
def generate_dashboard(payload: DashboardRequest):
    options = payload.options or {}
    result = service.generate(
        data=payload.data,
        gridfs_id=payload.gridfs_id,
        metadata=payload.metadata,
        **options
    )
    return clean_response(result)
