"""
Dashboard Designer Router
API endpoints for template-based dashboard generation
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from models.dashboard_models import (
    DashboardTemplate,
    ChartOptionsRequest,
    ChartOptionsResponse,
    SetSectionRequest,
    DashboardConfig,
    GenerateDashboardRequest,
    GenerateDashboardResponse
)
from services.dashboard_designer_service import DashboardDesignerService


router = APIRouter(prefix="/api/dashboard-designer", tags=["Dashboard Designer"])
service = DashboardDesignerService()


@router.get("/templates", response_model=List[DashboardTemplate])
async def get_templates():
    """
    Get all available dashboard templates
    
    Returns:
        List of dashboard templates with their sections
    """
    try:
        templates = service.get_all_templates()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve templates: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=DashboardTemplate)
async def get_template(template_id: str):
    """
    Get a specific template by ID
    
    Args:
        template_id: Template identifier
        
    Returns:
        DashboardTemplate with all sections
    """
    try:
        template = service.get_template_by_id(template_id)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve template: {str(e)}"
        )


@router.post("/chart-options", response_model=ChartOptionsResponse)
async def get_chart_options(request: ChartOptionsRequest):
    """
    Get available chart options for a specific section based on dataset
    
    Args:
        request: ChartOptionsRequest with dataset_id, template_id, section_id, and optional chart_type
        
    Returns:
        Available chart types, axis options, and aggregation functions
    """
    try:
        # Get chart options
        options = service.get_chart_options(
            dataset_id=request.dataset_id,
            section_id=request.section_id,
            template_id=request.template_id
        )
        
        return options
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chart options: {str(e)}"
        )


@router.post("/set-section", response_model=DashboardConfig)
async def set_section(request: SetSectionRequest):
    """
    Configure a specific section in a dashboard
    
    Args:
        request: SetSectionRequest with dashboard/template/section IDs and configuration
        
    Returns:
        Updated DashboardConfig with dashboard_id
        
    Note:
        - For chart sections: provide chart_config
        - For KPI sections: provide kpi_column and kpi_aggregation
        - First call creates new dashboard (returns dashboard_id)
        - Subsequent calls should include dashboard_id to update same dashboard
    """
    try:
        dashboard_config = service.set_section_config(
            dataset_id=request.dataset_id,
            template_id=request.template_id,
            section_id=request.section_id,
            chart_config=request.chart_config,
            kpi_column=request.kpi_column,
            kpi_aggregation=request.kpi_aggregation,
            dashboard_id=request.dashboard_id  # Pass dashboard_id from request
        )
        
        return dashboard_config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set section config: {str(e)}"
        )


@router.post("/generate", response_model=GenerateDashboardResponse)
async def generate_dashboard(request: GenerateDashboardRequest):
    """
    Generate a complete dashboard using AI
    
    Args:
        request: GenerateDashboardRequest with dataset_id and optional user_prompt
        
    Returns:
        Generated dashboard configuration with AI reasoning
    """
    try:
        response = service.generate_dashboard(
            dataset_id=request.dataset_id,
            user_prompt=request.user_prompt
        )
        
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard: {str(e)}"
        )


@router.get("/dashboard/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """
    Get a finalized dashboard with all charts and data
    
    Args:
        dashboard_id: Dashboard identifier
        
    Returns:
        Complete dashboard with KPIs and chart data
    """
    try:
        dashboard = service.finalize_dashboard(dashboard_id)
        return dashboard
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "dashboard-designer",
        "version": "1.0.0"
    }
