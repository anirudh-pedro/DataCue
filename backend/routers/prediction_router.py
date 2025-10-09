"""FastAPI router for prediction workflows."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from services.prediction_service import PredictionService
from shared.utils import clean_response

router = APIRouter(prefix="/prediction", tags=["prediction"])
service = PredictionService()


class TrainRequest(BaseModel):
    dataset_name: str = Field(..., description="Name of the dataset to train on")
    target_column: str = Field(..., description="Target column name")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional training options")


class PredictRequest(BaseModel):
    model_id: str = Field(..., description="Identifier of the trained model")
    features: List[Dict[str, Any]] = Field(..., description="Records to score")


@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    contents = await file.read()
    result = service.upload_dataset(filename=file.filename, content=contents)
    return clean_response(result)


@router.post("/train")
def train_model(request: TrainRequest):
    result = service.train(
        dataset_name=request.dataset_name,
        target_column=request.target_column,
        options=request.options,
    )
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Training failed"))
    return clean_response(result)


@router.post("/predict")
def predict(request: PredictRequest):
    result = service.predict(request.model_id, request.features)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return clean_response(result)


@router.get("/models")
def list_models():
    return service.list_models()


@router.get("/models/{model_id}/metadata")
def get_model_metadata(model_id: str):
    metadata = service.get_metadata(model_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Model metadata not found")
    return metadata
