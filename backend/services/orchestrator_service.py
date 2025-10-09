"""Composite service coordinating all agents for single-click workflows."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from services.dashboard_service import DashboardService
from services.ingestion_service import IngestionService
from services.knowledge_service import KnowledgeService
from services.prediction_service import PredictionService


class OrchestratorService:
    """Co-ordinates ingestion, dashboarding, knowledge and prediction agents."""

    def __init__(
        self,
        ingestion: Optional[IngestionService] = None,
        dashboard: Optional[DashboardService] = None,
        knowledge: Optional[KnowledgeService] = None,
        prediction: Optional[PredictionService] = None,
    ) -> None:
        self._ingestion = ingestion or IngestionService()
        self._dashboard = dashboard or DashboardService()
        self._knowledge = knowledge or KnowledgeService()
        self._prediction = prediction or PredictionService()

    def run_pipeline(
        self,
        *,
        filename: str,
        content: bytes,
        sheet_name: Optional[str] = None,
        target_column: Optional[str] = None,
        dashboard_options: Optional[Dict[str, Any]] = None,
        knowledge_options: Optional[Dict[str, Any]] = None,
        prediction_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an end-to-end workflow across all agents."""

        ingest_result = self._ingestion.ingest_file(
            filename=filename,
            content=content,
            sheet_name=sheet_name,
        )

        dataset_name = ingest_result.get("dataset_name")
        if ingest_result.get("status") != "success":
            return {
                "status": "error",
                "message": ingest_result.get("message", "Ingestion failed"),
                "ingestion": ingest_result,
            }

        data_records = deepcopy(ingest_result.get("data") or [])
        metadata = deepcopy(ingest_result.get("metadata") or {})

        pipeline: Dict[str, Any] = {
            "status": "success",
            "dataset_name": dataset_name,
            "steps": {
                "ingestion": {
                    key: ingest_result.get(key)
                    for key in (
                        "status",
                        "message",
                        "data_preview",
                        "metadata",
                        "dataset_name",
                        "original_shape",
                        "cleaned_shape",
                    )
                    if ingest_result.get(key) is not None
                },
            },
        }

        # Dashboard generation
        dashboard_payload = self._dashboard.generate(
            data=data_records,
            metadata=metadata,
            **(dashboard_options or {}),
        )
        pipeline["steps"]["dashboard"] = {
            "status": dashboard_payload.get("status"),
            "summary": dashboard_payload.get("summary"),
            "quality_indicators": dashboard_payload.get("quality_indicators"),
            "metadata_summary": dashboard_payload.get("metadata_summary"),
            "dashboard_id": dashboard_payload.get("dashboard_id"),
        }

        # Knowledge insights
        knowledge_opts = knowledge_options or {}
        knowledge_payload = self._knowledge.analyse(
            data=data_records,
            generate_insights=knowledge_opts.get("generate_insights", False),
            generate_recommendations=knowledge_opts.get("generate_recommendations", False),
        )
        pipeline["steps"]["knowledge"] = {
            "status": knowledge_payload.get("status"),
            "summary": knowledge_payload.get("summary"),
            "profile_basic_info": knowledge_payload.get("profile", {}).get("basic_info", {}),
            "recommendations": knowledge_payload.get("recommendations"),
        }

        # Optional prediction training
        if target_column:
            prediction_payload = self._prediction.train(
                dataset_name=dataset_name,
                target_column=target_column,
                options=prediction_options,
            )
            pipeline["steps"]["prediction"] = prediction_payload

        return pipeline
