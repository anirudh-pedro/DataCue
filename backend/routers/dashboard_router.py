"""FastAPI router exposing dashboard generation endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.dashboard_service import DashboardService
from shared.utils import clean_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = DashboardService()


class DashboardRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Dataset records")
    metadata: Dict[str, Any] = Field(..., description="Metadata extracted from ingestion agent")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Dashboard generation options")


@router.post("/generate")
def generate_dashboard(payload: DashboardRequest):
    options = payload.options or {}
    result = service.generate(payload.data, payload.metadata, **options)
    return clean_response(result)
