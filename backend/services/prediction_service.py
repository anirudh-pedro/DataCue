"""Service layer coordinating Prediction Agent workflows."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from agents.prediction_agent.prediction_agent import PredictionAgent
from models.registry import ModelRegistry
from shared import storage
from shared.utils import slugify


class PredictionService:
    def __init__(self) -> None:
        self._agent = PredictionAgent(models_dir=str(storage.MODELS_DIR))
        self._registry = ModelRegistry()

    def upload_dataset(self, filename: str, content: bytes) -> Dict[str, str]:
        dataset_name = slugify(filename.rsplit(".", 1)[0], fallback="dataset")
        storage.save_dataset(dataset_name, content)
        return {"dataset_name": dataset_name}

    def train(self, dataset_name: str, target_column: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        options = options or {}
        dataset_file = storage.dataset_path(dataset_name)
        if not dataset_file.exists():
            return {"status": "error", "message": f"Dataset '{dataset_name}' not found."}

        data = pd.read_csv(dataset_file)
        results = self._agent.auto_ml(
            data=data,
            target_column=target_column,
            problem_type=options.get("problem_type"),
            feature_engineering=options.get("feature_engineering", True),
            explain_model=options.get("explain_model", True),
            save_model=True,
            test_size=options.get("test_size", 0.2),
            random_state=options.get("random_state", 42),
        )

        if results.get("status") != "success":
            return results

        best_model_info = results["best_model"]
        model_path = best_model_info.get("model_path")
        if not model_path:
            return {"status": "error", "message": "Training completed but model path missing."}

        model_file = Path(model_path)
        model_id = model_file.stem
        # Normalise model file into registry metadata
        metadata = {
            "dataset_name": dataset_name,
            "target_column": target_column,
            "problem_type": results.get("problem_type"),
            "best_model": best_model_info,
            "models_trained": results.get("models_trained", []),
            "metrics": results.get("all_models"),
            "recommendations": results.get("recommendations", {}),
            "timestamp": results.get("timestamp") or datetime.utcnow().isoformat(),
        }

        self._registry.register(model_id=model_id, metadata=metadata)

        response = {
            "status": "success",
            "model_id": model_id,
            "model_path": model_path,
            "performance": best_model_info.get("metrics"),
            "metadata": metadata,
        }
        return response

    def predict(self, model_id: str, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        model_file = storage.model_path(model_id)
        if not model_file.exists():
            return {"status": "error", "message": f"Model '{model_id}' not found."}

        data = pd.DataFrame(features)
        return self._agent.predict(data=data, model_path=str(model_file))

    def list_models(self) -> Dict[str, Any]:
        records = self._registry.list_models()
        return {"models": records, "total": len(records)}

    def get_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self._registry.get(model_id)
