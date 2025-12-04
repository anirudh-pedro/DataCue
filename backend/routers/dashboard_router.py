"""FastAPI router exposing dashboard generation endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.dashboard_service import DashboardService
from services.dashboard_orchestration_service import get_orchestration_service
from services.component_query_service import get_component_query_service
from services.dataset_service import get_dataset_service
from shared.utils import clean_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = DashboardService()


class DashboardRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(default=None, description="Dataset records (optional if gridfs_id provided)")
    gridfs_id: str = Field(default=None, description="GridFS file ID of the dataset (optional if data provided)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata extracted from ingestion agent")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Dashboard generation options")


class ComponentSuggestionRequest(BaseModel):
    session_id: str = Field(..., description="Session ID for data isolation")
    dataset_id: str = Field(default=None, description="Optional dataset ID, uses latest if not provided")
    max_components: int = Field(default=6, description="Maximum number of components to suggest")


class ComponentDataRequest(BaseModel):
    session_id: str = Field(..., description="Session ID for data isolation")
    dataset_id: str = Field(..., description="Dataset ID")
    component: Dict[str, Any] = Field(..., description="Component configuration")


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


@router.post("/suggest-components")
def suggest_components(payload: ComponentSuggestionRequest):
    """
    Generate dashboard component suggestions based on dataset schema
    Uses Groq LLM to analyze columns and suggest appropriate visualizations
    """
    try:
        orchestration_service = get_orchestration_service()
        dataset_service = get_dataset_service()
        
        # Get dataset metadata (dataset_id is optional, gets latest if not provided)
        dataset_info = dataset_service.get_session_dataset(
            payload.session_id,
            payload.dataset_id
        )
        
        if not dataset_info:
            raise HTTPException(status_code=404, detail="Dataset not found for this session")
        
        # Use the dataset_id from the retrieved dataset info
        actual_dataset_id = dataset_info.get("dataset_id")
        
        # Get sample data for better suggestions
        sample_data = dataset_service.get_sample_rows(
            dataset_id=actual_dataset_id,
            session_id=payload.session_id,
            limit=5
        )
        
        # Generate suggestions
        suggestions = orchestration_service.suggest_dashboard_components(
            columns=dataset_info.get("columns", []),
            column_types=dataset_info.get("column_types", {}),
            sample_data=sample_data,
            max_components=payload.max_components
        )
        
        return {
            "success": True,
            "session_id": payload.session_id,
            "dataset_id": actual_dataset_id,
            "components": suggestions,
            "total_components": len(suggestions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@router.post("/component-data")
def get_component_data(payload: ComponentDataRequest):
    """
    Generate and execute MongoDB query for a specific dashboard component
    Returns data ready for visualization
    """
    try:
        query_service = get_component_query_service()
        dataset_service = get_dataset_service()
        
        # Get dataset metadata
        dataset_info = dataset_service.get_session_dataset(
            payload.session_id,
            payload.dataset_id
        )
        
        if not dataset_info:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Generate MongoDB query for this component
        pipeline = query_service.generate_component_query(
            component=payload.component,
            columns=dataset_info.get("columns", []),
            column_types=dataset_info.get("column_types", {}),
            session_id=payload.session_id,
            dataset_id=payload.dataset_id
        )
        
        if not pipeline:
            raise HTTPException(status_code=500, detail="Failed to generate query for component")
        
        # Execute query
        result = dataset_service.run_pipeline(
            session_id=payload.session_id,
            dataset_id=payload.dataset_id,
            pipeline=pipeline
        )
        
        return {
            "success": True,
            "component_id": payload.component.get("id"),
            "data": result,
            "pipeline": pipeline,
            "row_count": len(result) if isinstance(result, list) else 1
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch component data: {str(e)}")
