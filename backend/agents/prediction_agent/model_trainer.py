"""
Model Trainer
Handles the training of multiple ML models with proper error handling and timing.
"""

import time
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import logging
from importlib import import_module

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Trains multiple machine learning models and tracks performance metrics.
    """
    
    def __init__(self):
        """Initialize the model trainer"""
        self.trained_models = {}
        self.training_times = {}
    
    def train_models(
        self,
        models: List[Dict[str, Any]],
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        problem_type: str
    ) -> Dict[str, Any]:
        """
        Train multiple models and return results.
        
        Args:
            models: List of model configurations from ModelSelector
            X_train: Training features
            y_train: Training labels
            X_test: Test features
            y_test: Test labels
            problem_type: 'classification' or 'regression'
            
        Returns:
            Dictionary with trained models and training times
        """
        trained_models = {}
        training_times = {}
        errors = {}
        
        total_start = time.time()
        
        for model_config in models:
            model_name = model_config['name']
            config = model_config['config']
            
            try:
                logger.info(f"   Training {model_name}...")
                start_time = time.time()
                
                # Instantiate model
                model = self._instantiate_model(
                    class_path=config['class'],
                    params=config['params']
                )
                
                # Train model
                model.fit(X_train, y_train)
                
                # Calculate training time
                elapsed = time.time() - start_time
                training_times[model_name] = elapsed
                
                # Store trained model
                trained_models[model_name] = model
                
                logger.info(f"   ✓ {model_name} trained in {elapsed:.2f}s")
                
            except Exception as e:
                logger.error(f"   ✗ {model_name} failed: {str(e)}")
                errors[model_name] = str(e)
        
        total_time = time.time() - total_start
        
        logger.info(f"   Training completed in {total_time:.2f}s")
        
        return {
            'trained_models': trained_models,
            'training_times': training_times,
            'errors': errors,
            'total_time': total_time,
            'success_rate': len(trained_models) / len(models) if models else 0
        }
    
    def _instantiate_model(self, class_path: str, params: Dict[str, Any]):
        """
        Dynamically instantiate a model from class path.
        
        Args:
            class_path: e.g., 'sklearn.ensemble.RandomForestClassifier'
            params: Model parameters
            
        Returns:
            Instantiated model
        """
        # Parse module and class name
        module_path, class_name = class_path.rsplit('.', 1)
        
        # Import module
        module = import_module(module_path)
        
        # Get class
        model_class = getattr(module, class_name)
        
        # Instantiate with params
        return model_class(**params)
    
    def train_single_model(
        self,
        model_name: str,
        model_class: str,
        params: Dict[str, Any],
        X_train: np.ndarray,
        y_train: np.ndarray
    ):
        """
        Train a single model.
        
        Args:
            model_name: Name for the model
            model_class: Full class path
            params: Model parameters
            X_train: Training features
            y_train: Training labels
            
        Returns:
            Trained model
        """
        start_time = time.time()
        
        model = self._instantiate_model(model_class, params)
        model.fit(X_train, y_train)
        
        elapsed = time.time() - start_time
        
        self.trained_models[model_name] = model
        self.training_times[model_name] = elapsed
        
        return model
