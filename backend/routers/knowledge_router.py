"""Knowledge API router for visual Q&A with charts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.auth import FirebaseUser, get_current_user
from core.config import get_settings
from services.chat_query_service import ChatQueryService, get_chat_query_service
from services.dataset_service import DatasetService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
dataset_service = DatasetService()


class AskVisualRequest(BaseModel):
    """Request model for visual Q&A"""
    question: str = Field(..., description="Natural language question about the data")
    request_chart: bool = Field(default=True, description="Whether to generate a chart")
    session_id: Optional[str] = Field(default=None, description="Session ID for data lookup")
    dataset_id: Optional[str] = Field(default=None, description="Dataset ID")


class ChartResponse(BaseModel):
    """Chart response model"""
    chart_type: Optional[str] = None
    title: Optional[str] = None
    figure: Optional[Dict[str, Any]] = None


class AskVisualResponse(BaseModel):
    """Response model for visual Q&A"""
    answer: str
    chart: Optional[ChartResponse] = None
    data: Optional[List[Dict[str, Any]]] = None
    insight: Optional[str] = None


@router.post("/ask-visual", response_model=AskVisualResponse)
def ask_visual(
    payload: AskVisualRequest,
    current_user: FirebaseUser = Depends(get_current_user),
    query_service: ChatQueryService = Depends(get_chat_query_service),
) -> AskVisualResponse:
    """
    Ask a natural language question and optionally get a chart visualization.
    
    Returns both a text answer and an optional Plotly chart figure.
    """
    settings = get_settings()
    
    try:
        # Verify user owns the dataset if session_id is provided
        if payload.session_id and not settings.disable_firebase_auth:
            ownership = dataset_service.verify_ownership(
                session_id=payload.session_id,
                user_id=current_user.uid,
                dataset_id=payload.dataset_id
            )
            if not ownership["authorized"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ownership.get("reason", "Access denied to this dataset")
                )
        
        # Use chat query service to get the answer
        result = query_service.ask(
            question=payload.question,
            session_id=payload.session_id,
            dataset_id=payload.dataset_id,
        )
        
        # Handle error responses
        if result.get("status") == "error":
            return AskVisualResponse(
                answer=result.get("message", "Unable to process your question. Please try rephrasing."),
                chart=None,
                data=None,
                insight=None
            )
        
        # Build response
        answer = result.get("answer") or result.get("insight") or result.get("message") or "Analysis complete."
        data = result.get("data") or result.get("result")
        insight = result.get("insight")
        
        # Build chart if requested and data is available
        chart = None
        if payload.request_chart and data and isinstance(data, list) and len(data) > 0:
            chart = _build_chart_from_data(data, payload.question)
        
        return AskVisualResponse(
            answer=answer,
            chart=chart,
            data=data if isinstance(data, list) else None,
            insight=insight
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Return a friendly error message
        return AskVisualResponse(
            answer=f"I encountered an issue processing your question: {str(e)}",
            chart=None,
            data=None,
            insight=None
        )


def _build_chart_from_data(data: List[Dict[str, Any]], question: str) -> Optional[ChartResponse]:
    """Build a simple Plotly chart from query result data."""
    if not data or len(data) == 0:
        return None
    
    # Get column names
    columns = list(data[0].keys())
    if len(columns) < 2:
        return None
    
    # Determine chart type based on question keywords
    question_lower = question.lower()
    
    # Identify x and y columns (first column as x, second as y)
    x_col = columns[0]
    y_col = columns[1] if len(columns) > 1 else columns[0]
    
    # Extract values
    x_values = [row.get(x_col) for row in data]
    y_values = [row.get(y_col) for row in data]
    
    # Determine chart type
    if any(word in question_lower for word in ['trend', 'over time', 'monthly', 'yearly', 'daily']):
        chart_type = 'line'
    elif any(word in question_lower for word in ['distribution', 'breakdown', 'share', 'percentage']):
        chart_type = 'pie'
    elif any(word in question_lower for word in ['compare', 'comparison', 'vs', 'versus', 'top', 'bottom']):
        chart_type = 'bar'
    else:
        chart_type = 'bar'
    
    # Build Plotly figure
    if chart_type == 'pie':
        figure = {
            "data": [{
                "type": "pie",
                "labels": x_values,
                "values": y_values,
                "hole": 0.4,
                "marker": {
                    "colors": ["#118DFF", "#12B5CB", "#E66C37", "#B845A7", "#744EC2", "#D9B300"]
                }
            }],
            "layout": {
                "title": {"text": f"{y_col} by {x_col}", "font": {"color": "#e5e7eb"}},
                "paper_bgcolor": "transparent",
                "plot_bgcolor": "transparent",
                "font": {"color": "#9ca3af"},
                "showlegend": True,
                "legend": {"font": {"color": "#9ca3af"}}
            }
        }
    elif chart_type == 'line':
        figure = {
            "data": [{
                "type": "scatter",
                "mode": "lines+markers",
                "x": x_values,
                "y": y_values,
                "line": {"color": "#12B5CB", "width": 2},
                "marker": {"color": "#12B5CB", "size": 6},
                "fill": "tozeroy",
                "fillcolor": "rgba(18, 181, 203, 0.2)"
            }],
            "layout": {
                "title": {"text": f"{y_col} over {x_col}", "font": {"color": "#e5e7eb"}},
                "paper_bgcolor": "transparent",
                "plot_bgcolor": "transparent",
                "xaxis": {"title": x_col, "gridcolor": "rgba(75, 85, 99, 0.4)", "tickfont": {"color": "#9ca3af"}},
                "yaxis": {"title": y_col, "gridcolor": "rgba(75, 85, 99, 0.4)", "tickfont": {"color": "#9ca3af"}},
                "font": {"color": "#9ca3af"}
            }
        }
    else:  # bar chart
        figure = {
            "data": [{
                "type": "bar",
                "x": x_values,
                "y": y_values,
                "marker": {"color": "#118DFF"}
            }],
            "layout": {
                "title": {"text": f"{y_col} by {x_col}", "font": {"color": "#e5e7eb"}},
                "paper_bgcolor": "transparent",
                "plot_bgcolor": "transparent",
                "xaxis": {"title": x_col, "gridcolor": "rgba(75, 85, 99, 0.4)", "tickfont": {"color": "#9ca3af"}},
                "yaxis": {"title": y_col, "gridcolor": "rgba(75, 85, 99, 0.4)", "tickfont": {"color": "#9ca3af"}},
                "font": {"color": "#9ca3af"},
                "bargap": 0.3
            }
        }
    
    return ChartResponse(
        chart_type=chart_type,
        title=f"{y_col} by {x_col}",
        figure=figure
    )
