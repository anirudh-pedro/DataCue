"""
Prediction Agent (Agent 4) - ENTERPRISE EDITION
Automated machine learning pipeline for predictive analytics with advanced features.

This agent automatically:
- Detects problem type (classification/regression/clustering/timeseries)
- Selects appropriate algorithms (21+ models)
- Trains and evaluates models with cross-validation
- Tunes hyperparameters (GridSearch/RandomSearch/Optuna)
- Handles imbalanced data (SMOTE/ADASYN)
- Creates ensemble models (Voting/Stacking/Blending)
- Forecasts time series (ARIMA/Prophet)
- Monitors model performance and drift
- Provides feature importance and explainability (SHAP)
- Persists best models for inference
- Serves predictions via FastAPI
"""

from .prediction_agent import PredictionAgent
from .model_selector import ModelSelector
from .model_trainer import ModelTrainer
from .explainability_engine import ExplainabilityEngine
from .model_evaluator import ModelEvaluator
from .data_preprocessor import DataPreprocessor
from .feature_engineer import FeatureEngineer

# Enhanced Modules (v2.0)
from .cross_validator import CrossValidator
from .hyperparameter_tuner import HyperparameterTuner
from .cluster_evaluator import ClusterEvaluator
from .imbalanced_handler import ImbalancedDataHandler
from .ensemble_builder import EnsembleBuilder
from .time_series_forecaster import TimeSeriesForecaster
from .model_monitor import ModelMonitor

__all__ = [
    # Core Modules
    'PredictionAgent',
    'ModelSelector',
    'ModelTrainer',
    'ExplainabilityEngine',
    'ModelEvaluator',
    'DataPreprocessor',
    'FeatureEngineer',
    # Enhanced Modules
    'CrossValidator',
    'HyperparameterTuner',
    'ClusterEvaluator',
    'ImbalancedDataHandler',
    'EnsembleBuilder',
    'TimeSeriesForecaster',
    'ModelMonitor',
]

__version__ = '2.0.0'

