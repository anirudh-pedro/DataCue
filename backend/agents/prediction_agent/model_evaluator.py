"""
Model Evaluator
Evaluates trained models using appropriate metrics for classification and regression.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sklearn.metrics import (
    # Classification metrics
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    # Regression metrics
    mean_squared_error, mean_absolute_error, r2_score,
    mean_absolute_percentage_error
)
import logging

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Evaluates machine learning models using problem-specific metrics.
    """
    
    def __init__(self):
        """Initialize the evaluator"""
        pass
    
    def evaluate_all(
        self,
        trained_models: Dict[str, Any],
        X_test: np.ndarray,
        y_test: np.ndarray,
        problem_type: str
    ) -> Dict[str, Any]:
        """
        Evaluate all trained models and compare performance.
        
        Args:
            trained_models: Dictionary of trained models
            X_test: Test features
            y_test: Test labels
            problem_type: 'classification' or 'regression'
            
        Returns:
            Dictionary with metrics for all models and comparison
        """
        model_metrics = {}
        
        for model_name, model in trained_models.items():
            try:
                logger.info(f"   Evaluating {model_name}...")
                
                if problem_type == 'classification':
                    metrics = self._evaluate_classification(model, X_test, y_test)
                else:
                    metrics = self._evaluate_regression(model, X_test, y_test)
                
                model_metrics[model_name] = metrics
                
            except Exception as e:
                logger.error(f"   Error evaluating {model_name}: {str(e)}")
                model_metrics[model_name] = {'error': str(e)}
        
        # Create comparison DataFrame
        comparison_df = self._create_comparison_df(model_metrics, problem_type)
        
        # Identify best model
        best_model_name, best_score = self._identify_best_model(
            model_metrics, problem_type
        )
        
        return {
            'model_metrics': model_metrics,
            'comparison_df': comparison_df,
            'best_model_name': best_model_name,
            'best_score': best_score
        }
    
    def _evaluate_classification(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, Any]:
        """
        Evaluate classification model.
        
        Returns:
            Dictionary with classification metrics
        """
        # Predictions
        y_pred = model.predict(X_test)
        
        # Basic metrics
        accuracy = accuracy_score(y_test, y_pred)
        
        # Handle binary vs multiclass
        n_classes = len(np.unique(y_test))
        
        if n_classes == 2:
            # Binary classification
            precision = precision_score(y_test, y_pred, average='binary', zero_division=0)
            recall = recall_score(y_test, y_pred, average='binary', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='binary', zero_division=0)
            
            # ROC AUC (if predict_proba available)
            try:
                y_pred_proba = model.predict_proba(X_test)[:, 1]
                roc_auc = roc_auc_score(y_test, y_pred_proba)
            except:
                roc_auc = None
        else:
            # Multiclass
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            # ROC AUC for multiclass
            try:
                y_pred_proba = model.predict_proba(X_test)
                roc_auc = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
            except:
                roc_auc = None
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc) if roc_auc is not None else None,
            'confusion_matrix': cm.tolist(),
            'n_classes': int(n_classes),
            'support': int(len(y_test))
        }
    
    def _evaluate_regression(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, Any]:
        """
        Evaluate regression model.
        
        Returns:
            Dictionary with regression metrics
        """
        # Predictions
        y_pred = model.predict(X_test)
        
        # Metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # MAPE (handle division by zero)
        try:
            mape = mean_absolute_percentage_error(y_test, y_pred)
        except:
            mape = None
        
        # Adjusted R²
        n = len(y_test)
        p = X_test.shape[1]
        adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1) if n > p + 1 else None
        
        return {
            'r2_score': float(r2),
            'adjusted_r2': float(adj_r2) if adj_r2 is not None else None,
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape) if mape is not None else None,
            'support': int(len(y_test))
        }
    
    def _create_comparison_df(
        self,
        model_metrics: Dict[str, Dict[str, Any]],
        problem_type: str
    ) -> pd.DataFrame:
        """
        Create a comparison DataFrame for easy model comparison.
        
        Returns:
            DataFrame with model names as rows and metrics as columns
        """
        data = []
        
        for model_name, metrics in model_metrics.items():
            if 'error' in metrics:
                continue
            
            row = {'Model': model_name}
            
            if problem_type == 'classification':
                row.update({
                    'Accuracy': metrics.get('accuracy', 0),
                    'Precision': metrics.get('precision', 0),
                    'Recall': metrics.get('recall', 0),
                    'F1 Score': metrics.get('f1_score', 0),
                    'ROC AUC': metrics.get('roc_auc', 0)
                })
            else:
                row.update({
                    'R² Score': metrics.get('r2_score', 0),
                    'RMSE': metrics.get('rmse', 0),
                    'MAE': metrics.get('mae', 0),
                    'MAPE': metrics.get('mape', 0)
                })
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Sort by primary metric (descending for better metrics)
        if problem_type == 'classification':
            if 'Accuracy' in df.columns:
                df = df.sort_values('Accuracy', ascending=False)
        else:
            if 'R² Score' in df.columns:
                df = df.sort_values('R² Score', ascending=False)
        
        return df.reset_index(drop=True)
    
    def _identify_best_model(
        self,
        model_metrics: Dict[str, Dict[str, Any]],
        problem_type: str
    ) -> tuple:
        """
        Identify the best performing model.
        
        Returns:
            Tuple of (best_model_name, best_score)
        """
        best_model = None
        best_score = -np.inf if problem_type == 'classification' or problem_type == 'regression' else np.inf
        
        for model_name, metrics in model_metrics.items():
            if 'error' in metrics:
                continue
            
            if problem_type == 'classification':
                score = metrics.get('accuracy', 0)
                if score > best_score:
                    best_score = score
                    best_model = model_name
            else:
                score = metrics.get('r2_score', -np.inf)
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        return best_model, best_score
    
    def evaluate_single_model(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray,
        problem_type: str
    ) -> Dict[str, Any]:
        """
        Evaluate a single model.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            problem_type: 'classification' or 'regression'
            
        Returns:
            Dictionary with metrics
        """
        if problem_type == 'classification':
            return self._evaluate_classification(model, X_test, y_test)
        else:
            return self._evaluate_regression(model, X_test, y_test)
