"""
Prediction API
FastAPI endpoints for model training, prediction, and explanation.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DataCue Prediction API",
    description="Machine Learning Model Training and Inference API",
    version="1.0.0"
)

# Request/Response Models
class TrainRequest(BaseModel):
    """Training request model"""
    dataset_name: str = Field(..., description="Name of dataset")
    target_column: str = Field(..., description="Target variable column name")
    problem_type: Optional[str] = Field(None, description="classification or regression")
    feature_engineering: bool = Field(True, description="Apply feature engineering")
    handle_imbalance: bool = Field(False, description="Handle imbalanced data")
    use_cross_validation: bool = Field(True, description="Use cross-validation")
    tune_hyperparameters: bool = Field(False, description="Tune hyperparameters")
    create_ensemble: bool = Field(False, description="Create ensemble model")

class PredictRequest(BaseModel):
    """Prediction request model"""
    model_id: str = Field(..., description="Model identifier")
    features: List[Dict[str, Any]] = Field(..., description="Feature data")
    
class ExplainRequest(BaseModel):
    """Explanation request model"""
    model_id: str = Field(..., description="Model identifier")
    features: Dict[str, Any] = Field(..., description="Single instance features")

class TrainResponse(BaseModel):
    """Training response model"""
    model_id: str
    best_model: str
    performance: Dict[str, Any]
    status: str
    message: str

class PredictResponse(BaseModel):
    """Prediction response model"""
    predictions: List[Any]
    model_id: str
    timestamp: str

# Global model registry (in production, use database)
MODEL_REGISTRY: Dict[str, Any] = {}
MODELS_DIR = Path("./saved_models")
MODELS_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "healthy",
        "api": "DataCue Prediction API",
        "version": "1.0.0"
    }


@app.post("/train", response_model=TrainResponse)
async def train_model(
    request: TrainRequest,
    background_tasks: BackgroundTasks
):
    """
    Train a new ML model.
    
    - Loads dataset
    - Preprocesses data
    - Trains models
    - Returns best model
    """
    try:
        from ...prediction_agent import PredictionAgent
        
        logger.info(f"Training request received for dataset: {request.dataset_name}")
        
        # Initialize agent
        agent = PredictionAgent()
        
        # Load dataset (simplified - in production, implement proper data loading)
        # For now, assume data is uploaded separately
        data_path = f"./data/{request.dataset_name}.csv"
        if not Path(data_path).exists():
            raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_name} not found")
        
        data = pd.read_csv(data_path)
        
        # Run AutoML
        results = agent.auto_ml(
            data=data,
            target_column=request.target_column,
            problem_type=request.problem_type,
            feature_engineering=request.feature_engineering,
            handle_imbalance=request.handle_imbalance,
            use_cross_validation=request.use_cross_validation,
            tune_hyperparameters=request.tune_hyperparameters,
            create_ensemble=request.create_ensemble
        )
        
        # Generate model ID
        from datetime import datetime
        model_id = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save model
        model_path = MODELS_DIR / f"{model_id}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(results['best_model'], f)
        
        # Register model
        MODEL_REGISTRY[model_id] = {
            'model': results['best_model'],
            'metadata': results['metadata'],
            'problem_type': results['problem_type']
        }
        
        return TrainResponse(
            model_id=model_id,
            best_model=results['best_model_name'],
            performance=results['performance'],
            status="success",
            message=f"Model trained successfully with {results['best_model_name']}"
        )
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Make predictions using trained model.
    
    - Loads model
    - Preprocesses input
    - Returns predictions
    """
    try:
        from datetime import datetime
        
        # Check if model exists
        if request.model_id not in MODEL_REGISTRY:
            # Try loading from disk
            model_path = MODELS_DIR / f"{request.model_id}.pkl"
            if not model_path.exists():
                raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found")
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
                MODEL_REGISTRY[request.model_id] = {'model': model}
        
        model_info = MODEL_REGISTRY[request.model_id]
        model = model_info['model']
        
        # Convert features to DataFrame
        df = pd.DataFrame(request.features)
        
        # Make predictions
        predictions = model.predict(df)
        
        return PredictResponse(
            predictions=predictions.tolist(),
            model_id=request.model_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain")
async def explain_prediction(request: ExplainRequest):
    """
    Explain model prediction using SHAP.
    
    - Loads model
    - Generates SHAP explanations
    - Returns feature importance
    """
    try:
        # Check if model exists
        if request.model_id not in MODEL_REGISTRY:
            raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found")
        
        model_info = MODEL_REGISTRY[request.model_id]
        
        # Use explainability engine
        from ..explainability_engine import ExplainabilityEngine
        
        explainer = ExplainabilityEngine()
        
        # Convert to array
        X = pd.DataFrame([request.features]).values
        
        # Generate explanation
        explanation = explainer.explain(
            model=model_info['model'],
            X_test=X,
            X_train=None,  # Would need to store this
            feature_names=list(request.features.keys())
        )
        
        return JSONResponse(content=explanation)
        
    except Exception as e:
        logger.error(f"Explanation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """List all available models"""
    models_info = []
    
    for model_id, info in MODEL_REGISTRY.items():
        models_info.append({
            'model_id': model_id,
            'problem_type': info.get('problem_type', 'unknown'),
            'metadata': info.get('metadata', {})
        })
    
    return {
        'models': models_info,
        'total': len(models_info)
    }


@app.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """Delete a model"""
    if model_id not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    
    # Remove from registry
    del MODEL_REGISTRY[model_id]
    
    # Delete file
    model_path = MODELS_DIR / f"{model_id}.pkl"
    if model_path.exists():
        model_path.unlink()
    
    return {"message": f"Model {model_id} deleted successfully"}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "models_loaded": len(MODEL_REGISTRY),
        "models_directory": str(MODELS_DIR),
        "api_version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
