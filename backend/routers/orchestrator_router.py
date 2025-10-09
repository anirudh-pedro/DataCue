"""Router exposing single-click orchestration flows."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from services.orchestrator_service import OrchestratorService
from shared.utils import clean_response

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])
service = OrchestratorService()


@router.post("/pipeline")
async def run_pipeline(
    file: UploadFile = File(..., description="Dataset file (CSV or Excel)"),
    sheet_name: Optional[str] = Form(default=None),
    target_column: Optional[str] = Form(default=None, description="Column to use as prediction target"),
    dashboard_type: str = Form(default="auto"),
    include_advanced_charts: bool = Form(default=True),
    generate_dashboard_insights: bool = Form(default=True),
    knowledge_generate_insights: bool = Form(default=False),
    knowledge_generate_recommendations: bool = Form(default=False),
    prediction_options_json: Optional[str] = Form(default=None, description="JSON object with extra prediction options"),
):
    try:
        contents = await file.read()
        prediction_options: Optional[Dict[str, Any]] = None
        if prediction_options_json:
            try:
                prediction_options = json.loads(prediction_options_json)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise HTTPException(status_code=400, detail=f"Invalid prediction options JSON: {exc}") from exc

        dashboard_options = {
            "dashboard_type": dashboard_type,
            "include_advanced_charts": include_advanced_charts,
            "generate_insights": generate_dashboard_insights,
        }
        knowledge_options = {
            "generate_insights": knowledge_generate_insights,
            "generate_recommendations": knowledge_generate_recommendations,
        }

        result = service.run_pipeline(
            filename=file.filename or "dataset.csv",
            content=contents,
            sheet_name=sheet_name,
            target_column=target_column,
            dashboard_options=dashboard_options,
            knowledge_options=knowledge_options,
            prediction_options=prediction_options,
        )
        return clean_response(result)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc
