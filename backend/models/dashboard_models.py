"""
Dashboard Designer Models
Pydantic models for template-based dashboard generation
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class ChartType(str, Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    BOX = "box"
    HEATMAP = "heatmap"
    AREA = "area"
    FUNNEL = "funnel"
    TREEMAP = "treemap"


class SectionType(str, Enum):
    """Dashboard section types"""
    HEADER = "header"
    KPI = "kpi"
    CHART = "chart"
    TABLE = "table"
    TEXT = "text"


class ChartOption(BaseModel):
    """Chart configuration option"""
    chart_type: ChartType
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    color_by: Optional[str] = None
    aggregation: Optional[str] = "sum"  # sum, count, avg, min, max
    title: Optional[str] = None
    description: Optional[str] = None


class TemplateSection(BaseModel):
    """Template section definition"""
    section_id: str
    section_type: SectionType
    title: str
    description: str
    position: int  # Layout position (0-based)
    size: str = "medium"  # small, medium, large, full
    required: bool = True
    default_chart_type: Optional[ChartType] = None
    allowed_chart_types: List[ChartType] = []
    chart_config: Optional[ChartOption] = None  # User's selected configuration


class DashboardTemplate(BaseModel):
    """Dashboard template definition"""
    template_id: str
    name: str
    description: str
    category: str
    icon: str = "📊"
    sections: List[TemplateSection]
    layout_type: str = "grid"  # grid, stack, masonry
    color_scheme: str = "default"


class DatasetInfo(BaseModel):
    """Dataset metadata for analysis"""
    dataset_id: str
    columns: List[str]
    column_types: Dict[str, str]  # column_name -> type (numeric, categorical, datetime)
    row_count: int
    sample_data: Optional[Dict[str, List[Any]]] = None


class ChartOptionsRequest(BaseModel):
    """Request for chart options based on data"""
    dataset_id: str
    template_id: str
    section_id: str
    chart_type: Optional[ChartType] = None


class ChartOptionsResponse(BaseModel):
    """Available chart options for a section"""
    section_id: str
    available_chart_types: List[ChartType]
    x_axis_options: List[str]
    y_axis_options: List[str]
    color_options: List[str]
    aggregation_options: List[str] = ["sum", "count", "avg", "min", "max"]


class SetSectionRequest(BaseModel):
    """Request to configure a dashboard section"""
    dataset_id: str
    template_id: str
    section_id: str
    chart_config: ChartOption


class DashboardConfig(BaseModel):
    """Complete dashboard configuration"""
    dashboard_id: str
    template_id: str
    dataset_id: str
    title: str
    description: Optional[str] = None
    sections: List[TemplateSection]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GenerateDashboardRequest(BaseModel):
    """Request for AI-generated dashboard"""
    dataset_id: str
    user_prompt: Optional[str] = None  # Optional guidance for AI


class GenerateDashboardResponse(BaseModel):
    """Response with generated dashboard configuration"""
    dashboard_id: str
    config: DashboardConfig
    ai_reasoning: Optional[str] = None  # Why AI chose these charts
