"""
Frontend Contract Models
Defines strict JSON schemas for API responses that the frontend expects
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum


# ============== CHART TYPES ==============

class ChartType(str, Enum):
    """Supported chart types for frontend rendering"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    AREA = "area"


# ============== RESULT TYPES ==============

class ResultType(str, Enum):
    """Types of results from chat queries"""
    KPI = "kpi"
    TABLE = "table"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    TEXT = "text"


# ============== DASHBOARD CONTRACTS ==============

class ChartConfig(BaseModel):
    """Configuration for a single chart in the dashboard"""
    chart_id: str = Field(..., description="Unique chart identifier")
    chart_type: ChartType = Field(..., description="Type of chart to render")
    title: str = Field(..., description="Chart title")
    description: Optional[str] = Field(None, description="Chart description")
    x_axis: Optional[str] = Field(None, description="Column for x-axis")
    y_axis: Optional[str] = Field(None, description="Column for y-axis")
    aggregation: Optional[str] = Field("sum", description="Aggregation method")
    

class ChartData(BaseModel):
    """Data for a single chart"""
    labels: Optional[List[str]] = Field(None, description="X-axis labels (for bar/pie)")
    values: Optional[List[float]] = Field(None, description="Y-axis values")
    x: Optional[List[Any]] = Field(None, description="X values (for line/scatter)")
    y: Optional[List[float]] = Field(None, description="Y values (for line/scatter)")


class DashboardChart(BaseModel):
    """Complete chart with config and data"""
    chart_id: str
    chart_type: str
    title: str
    description: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    aggregation: Optional[str] = "sum"
    data: List[Dict[str, Any]] = Field(..., description="Chart data records")


class DashboardResponse(BaseModel):
    """
    Dashboard API Response Contract
    
    Frontend expects this exact structure from /dashboard/generate
    """
    status: Literal["success", "error"]
    dashboard: Optional[Dict[str, Any]] = Field(None, description="Dashboard configuration")
    insights: Optional[List[str]] = Field(None, description="Key insights about the data")
    message: Optional[str] = Field(None, description="Error message if status is error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "dashboard": {
                    "dashboard_id": "dashboard_abc123",
                    "title": "Sales Dashboard",
                    "description": "Overview of sales performance",
                    "charts": [
                        {
                            "chart_id": "chart_001",
                            "chart_type": "bar",
                            "title": "Revenue by Region",
                            "x_axis": "region",
                            "y_axis": "revenue",
                            "aggregation": "sum",
                            "data": [
                                {"region": "North", "revenue": 50000},
                                {"region": "South", "revenue": 45000}
                            ]
                        }
                    ]
                },
                "insights": [
                    "North region has the highest revenue",
                    "Sales peaked in Q4"
                ]
            }
        }


# ============== CHAT CONTRACTS ==============

class KPIResult(BaseModel):
    """KPI/single number result"""
    value: float
    formatted: str = Field(..., description="Human-readable formatted value")


class TableResult(BaseModel):
    """Table result"""
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int


class ChartResult(BaseModel):
    """Chart result for visualization"""
    labels: Optional[List[str]] = None
    values: Optional[List[float]] = None
    x: Optional[List[Any]] = None
    y: Optional[List[float]] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None


class ChatChartConfig(BaseModel):
    """Chart configuration for chat response"""
    chart_type: str
    title: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None


class ChatResponse(BaseModel):
    """
    Chat API Response Contract
    
    Frontend expects this exact structure from /chat/ask
    """
    status: Literal["success", "error"]
    question: Optional[str] = Field(None, description="Original question")
    result: Optional[Any] = Field(None, description="Query result data")
    result_type: Optional[ResultType] = Field(None, description="Type of result for rendering")
    chart_config: Optional[Dict[str, Any]] = Field(None, description="Chart config if result is a chart")
    insight: Optional[str] = Field(None, description="AI-generated insight about the result")
    query_used: Optional[str] = Field(None, description="The pandas query that was executed")
    query_type: Optional[str] = Field(None, description="Type of query: aggregation, filter, groupby")
    message: Optional[str] = Field(None, description="Error message if status is error")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "name": "KPI Result",
                    "value": {
                        "status": "success",
                        "question": "What is the total revenue?",
                        "result": {"value": 150000.0, "formatted": "$150.00K"},
                        "result_type": "kpi",
                        "insight": "Total revenue across all regions",
                        "query_used": "df['revenue'].sum()"
                    }
                },
                {
                    "name": "Table Result",
                    "value": {
                        "status": "success",
                        "question": "Show top 5 products",
                        "result": {
                            "columns": ["product", "sales"],
                            "rows": [{"product": "Widget A", "sales": 500}],
                            "total_rows": 5
                        },
                        "result_type": "table",
                        "insight": "Top products by sales volume"
                    }
                },
                {
                    "name": "Line Chart Result",
                    "value": {
                        "status": "success",
                        "question": "Revenue trend over time",
                        "result": {
                            "x": ["2024-01", "2024-02", "2024-03"],
                            "y": [10000, 15000, 12000],
                            "x_label": "month",
                            "y_label": "revenue"
                        },
                        "result_type": "line_chart",
                        "chart_config": {
                            "chart_type": "line",
                            "x_axis": "month",
                            "y_axis": "revenue",
                            "title": "Revenue over time"
                        }
                    }
                },
                {
                    "name": "Bar Chart Result", 
                    "value": {
                        "status": "success",
                        "question": "Sales by region",
                        "result": {
                            "labels": ["North", "South", "East", "West"],
                            "values": [50000, 45000, 40000, 35000],
                            "x_label": "region",
                            "y_label": "sales"
                        },
                        "result_type": "bar_chart",
                        "chart_config": {
                            "chart_type": "bar",
                            "x_axis": "region",
                            "y_axis": "sales"
                        }
                    }
                }
            ]
        }


# ============== INGESTION CONTRACTS ==============

class ColumnMetadata(BaseModel):
    """Metadata for a single column"""
    name: str
    type: Literal["numeric", "categorical", "datetime"]
    unique_count: int
    null_count: int


class DatasetMetadata(BaseModel):
    """Complete dataset metadata"""
    columns: List[ColumnMetadata]
    row_count: int
    column_count: int


class IngestionResponse(BaseModel):
    """
    Ingestion API Response Contract
    
    Frontend expects this from /ingestion/upload
    """
    status: Literal["success", "error"]
    message: str
    dataset_name: Optional[str] = None
    gridfs_id: Optional[str] = None
    dataset_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[DatasetMetadata] = None
    shape: Optional[Dict[str, int]] = Field(None, description="{'rows': N, 'columns': M}")
    column_fixes: Optional[List[Dict[str, str]]] = Field(None, description="Columns that were auto-fixed")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Cleaned dataset records")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "File ingested successfully",
                "dataset_name": "sales_data",
                "gridfs_id": "507f1f77bcf86cd799439011",
                "dataset_id": "uuid-123",
                "session_id": "session-456",
                "metadata": {
                    "columns": [
                        {"name": "product", "type": "categorical", "unique_count": 50, "null_count": 0},
                        {"name": "revenue", "type": "numeric", "unique_count": 100, "null_count": 2}
                    ],
                    "row_count": 1000,
                    "column_count": 5
                },
                "shape": {"rows": 1000, "columns": 5},
                "column_fixes": [
                    {"original": "Unnamed: 0", "fixed": "row_index"}
                ]
            }
        }
