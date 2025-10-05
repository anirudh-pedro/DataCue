"""
Prediction Agent - Main Orchestrator
Coordinates model selection, training, evaluation, and explainability.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import pickle
import json
from pathlib import Path

from .model_selector import ModelSelector
from .model_trainer import ModelTrainer
from .model_evaluator import ModelEvaluator
from .explainability_engine import ExplainabilityEngine
from .feature_engineer import FeatureEngineer
from .data_preprocessor import DataPreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionAgent:
    """
    Main orchestrator for automated machine learning pipeline.
    
    Workflow:
    1. Analyze dataset and detect problem type
    2. Preprocess data (encoding, scaling)
    3. Select appropriate algorithms
    4. Train multiple models
    5. Evaluate and compare
    6. Generate explainability insights
    7. Save best model
    """
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize the Prediction Agent.
        
        Args:
            models_dir: Directory to save trained models
        """
        self.model_selector = ModelSelector()
        self.model_trainer = ModelTrainer()
        self.model_evaluator = ModelEvaluator()
        self.explainability_engine = ExplainabilityEngine()
        self.feature_engineer = FeatureEngineer()
        self.preprocessor = DataPreprocessor()
        
        # Create models directory
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # State
        self.problem_type = None
        self.target_column = None
        self.trained_models = {}
        self.best_model = None
        self.best_model_name = None
        self.feature_names = None
        self.preprocessor_state = None
    
    def auto_ml(
        self,
        data: pd.DataFrame,
        target_column: str,
        problem_type: Optional[str] = None,
        test_size: float = 0.2,
        feature_engineering: bool = True,
        explain_model: bool = True,
        save_model: bool = True,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Complete automated ML pipeline.
        
        Args:
            data: Input DataFrame
            target_column: Name of target variable
            problem_type: 'classification', 'regression', or None (auto-detect)
            test_size: Proportion of data for testing (0.0-1.0)
            feature_engineering: Whether to perform automated feature engineering
            explain_model: Whether to generate SHAP explanations
            save_model: Whether to save the best model
            random_state: Random seed for reproducibility
            
        Returns:
            Complete analysis results with models, metrics, and insights
        """
        logger.info("🚀 Starting AutoML Pipeline...")
        start_time = datetime.now()
        
        try:
            # Validate inputs
            self._validate_inputs(data, target_column)
            self.target_column = target_column
            
            # Step 1: Detect problem type
            logger.info("📊 Step 1/7: Detecting problem type...")
            if problem_type is None:
                self.problem_type = self._detect_problem_type(data[target_column])
            else:
                self.problem_type = problem_type.lower()
            
            logger.info(f"   Problem Type: {self.problem_type.upper()}")
            
            # Step 2: Feature engineering (optional)
            if feature_engineering:
                logger.info("⚙️  Step 2/7: Engineering features...")
                data = self.feature_engineer.engineer_features(data, self.problem_type)
                logger.info(f"   Features: {len(data.columns) - 1} total")
            else:
                logger.info("⏭️  Step 2/7: Skipping feature engineering...")
            
            # Step 3: Preprocess data
            logger.info("🔧 Step 3/7: Preprocessing data...")
            X_train, X_test, y_train, y_test, preprocessor_info = self.preprocessor.preprocess(
                data=data,
                target_column=target_column,
                problem_type=self.problem_type,
                test_size=test_size,
                random_state=random_state
            )
            
            self.feature_names = preprocessor_info['feature_names']
            self.preprocessor_state = preprocessor_info
            logger.info(f"   Train: {len(X_train)} samples, Test: {len(X_test)} samples")
            
            # Step 4: Select models
            logger.info("🎯 Step 4/7: Selecting algorithms...")
            selected_models = self.model_selector.select_models(
                problem_type=self.problem_type,
                n_samples=len(X_train),
                n_features=X_train.shape[1]
            )
            logger.info(f"   Selected {len(selected_models)} algorithms")
            
            # Step 5: Train models
            logger.info("🏋️  Step 5/7: Training models...")
            training_results = self.model_trainer.train_models(
                models=selected_models,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                problem_type=self.problem_type
            )
            
            self.trained_models = training_results['trained_models']
            logger.info(f"   Trained {len(self.trained_models)} models successfully")
            
            # Step 6: Evaluate and compare
            logger.info("📈 Step 6/7: Evaluating models...")
            evaluation_results = self.model_evaluator.evaluate_all(
                trained_models=self.trained_models,
                X_test=X_test,
                y_test=y_test,
                problem_type=self.problem_type
            )
            
            # Select best model
            self.best_model_name = evaluation_results['best_model_name']
            self.best_model = self.trained_models[self.best_model_name]
            logger.info(f"   Best Model: {self.best_model_name}")
            
            # Step 7: Generate explanations
            explanations = {}
            if explain_model:
                logger.info("💡 Step 7/7: Generating explainability insights...")
                try:
                    explanations = self.explainability_engine.explain(
                        model=self.best_model,
                        X_train=X_train,
                        X_test=X_test,
                        feature_names=self.feature_names,
                        problem_type=self.problem_type
                    )
                    logger.info("   Explanations generated successfully")
                except Exception as e:
                    logger.warning(f"   Could not generate explanations: {str(e)}")
                    explanations = {"error": str(e)}
            else:
                logger.info("⏭️  Step 7/7: Skipping explainability...")
            
            # Save best model
            model_path = None
            if save_model:
                model_path = self._save_model(
                    model=self.best_model,
                    model_name=self.best_model_name,
                    preprocessor_info=preprocessor_info
                )
                logger.info(f"   Model saved to: {model_path}")
            
            # Calculate elapsed time
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                evaluation_results=evaluation_results,
                explanations=explanations,
                data=data
            )
            
            logger.info(f"✅ AutoML Complete! ({elapsed_time:.2f}s)\n")
            
            # Return comprehensive results
            return {
                'status': 'success',
                'problem_type': self.problem_type,
                'target_column': target_column,
                'dataset_info': {
                    'total_samples': len(data),
                    'train_samples': len(X_train),
                    'test_samples': len(X_test),
                    'n_features': X_train.shape[1],
                    'feature_names': self.feature_names
                },
                'models_trained': list(self.trained_models.keys()),
                'best_model': {
                    'name': self.best_model_name,
                    'metrics': evaluation_results['model_metrics'][self.best_model_name],
                    'model_path': str(model_path) if model_path else None
                },
                'all_models': evaluation_results['model_metrics'],
                'model_comparison': evaluation_results['comparison_df'].to_dict('records'),
                'explainability': explanations,
                'recommendations': recommendations,
                'preprocessing_info': preprocessor_info,
                'training_time': training_results['total_time'],
                'total_time': elapsed_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ AutoML Pipeline Failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f"AutoML failed: {str(e)}",
                'error_details': traceback.format_exc()
            }
    
    def predict(
        self,
        data: pd.DataFrame,
        model_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make predictions using a trained model.
        
        Args:
            data: New data to predict on
            model_path: Path to saved model (if None, uses best_model in memory)
            
        Returns:
            Predictions with probabilities (for classification)
        """
        try:
            # Load model if path provided
            if model_path:
                model_info = self._load_model(model_path)
                model = model_info['model']
                preprocessor_info = model_info['preprocessor_info']
            else:
                if self.best_model is None:
                    raise ValueError("No model available. Train a model first or provide model_path.")
                model = self.best_model
                preprocessor_info = self.preprocessor_state
            
            # Preprocess new data
            X_processed = self.preprocessor.preprocess_new_data(
                data=data,
                preprocessor_info=preprocessor_info
            )
            
            # Make predictions
            predictions = model.predict(X_processed)
            
            result = {
                'predictions': predictions.tolist(),
                'n_samples': len(predictions)
            }
            
            # Add probabilities for classification
            if self.problem_type == 'classification' and hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X_processed)
                result['probabilities'] = probabilities.tolist()
                result['classes'] = model.classes_.tolist() if hasattr(model, 'classes_') else None
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return {
                'status': 'error',
                'message': f"Prediction failed: {str(e)}"
            }
    
    def _validate_inputs(self, data: pd.DataFrame, target_column: str):
        """Validate input data and target column"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame")
        
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        if len(data) < 10:
            raise ValueError("Dataset too small. Need at least 10 samples.")
        
        # Check for sufficient non-null values
        if data[target_column].isnull().sum() / len(data) > 0.5:
            raise ValueError(f"Target column has >50% missing values")
    
    def _detect_problem_type(self, target: pd.Series) -> str:
        """
        Automatically detect problem type based on target variable.
        
        Returns:
            'classification' or 'regression'
        """
        # Remove nulls
        target_clean = target.dropna()
        
        # Check if numeric
        if pd.api.types.is_numeric_dtype(target_clean):
            unique_ratio = target_clean.nunique() / len(target_clean)
            
            # If fewer than 20 unique values or unique ratio < 0.05, likely classification
            if target_clean.nunique() <= 20 or unique_ratio < 0.05:
                return 'classification'
            else:
                return 'regression'
        else:
            # Non-numeric = classification
            return 'classification'
    
    def _save_model(
        self,
        model,
        model_name: str,
        preprocessor_info: Dict[str, Any]
    ) -> Path:
        """Save trained model and preprocessing info"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{model_name}_{self.problem_type}_{timestamp}.pkl"
        filepath = self.models_dir / filename
        
        model_package = {
            'model': model,
            'model_name': model_name,
            'problem_type': self.problem_type,
            'target_column': self.target_column,
            'preprocessor_info': preprocessor_info,
            'feature_names': self.feature_names,
            'timestamp': timestamp
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_package, f)
        
        # Also save metadata as JSON
        metadata = {
            'model_name': model_name,
            'problem_type': self.problem_type,
            'target_column': self.target_column,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'timestamp': timestamp,
            'model_file': filename
        }
        
        metadata_path = self.models_dir / f"{model_name}_{self.problem_type}_{timestamp}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return filepath
    
    def _load_model(self, model_path: str) -> Dict[str, Any]:
        """Load a saved model"""
        with open(model_path, 'rb') as f:
            model_package = pickle.load(f)
        
        return model_package
    
    def _generate_recommendations(
        self,
        evaluation_results: Dict[str, Any],
        explanations: Dict[str, Any],
        data: pd.DataFrame
    ) -> Dict[str, List[str]]:
        """Generate actionable recommendations based on results"""
        recommendations = {
            'model_improvement': [],
            'feature_engineering': [],
            'data_quality': [],
            'next_steps': []
        }
        
        best_score = evaluation_results['best_score']
        
        # Model improvement suggestions
        if self.problem_type == 'classification':
            if best_score < 0.7:
                recommendations['model_improvement'].append(
                    "Model performance is below 70% accuracy. Consider collecting more data or improving features."
                )
            elif best_score < 0.85:
                recommendations['model_improvement'].append(
                    "Good performance. Try hyperparameter tuning to improve further."
                )
            else:
                recommendations['model_improvement'].append(
                    "Excellent performance! Consider ensemble methods or deep learning for marginal gains."
                )
        else:  # regression
            if best_score < 0.5:
                recommendations['model_improvement'].append(
                    "R² below 0.5 indicates weak predictive power. Review feature selection."
                )
            elif best_score < 0.8:
                recommendations['model_improvement'].append(
                    "Moderate performance. Try polynomial features or interaction terms."
                )
        
        # Feature engineering
        if 'feature_importance' in explanations:
            top_features = explanations.get('top_features', [])
            if len(top_features) > 0:
                recommendations['feature_engineering'].append(
                    f"Focus on top features: {', '.join(top_features[:3])}"
                )
        
        # Data quality
        missing_pct = data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100
        if missing_pct > 5:
            recommendations['data_quality'].append(
                f"Dataset has {missing_pct:.1f}% missing values. Consider better imputation strategies."
            )
        
        if len(data) < 1000:
            recommendations['data_quality'].append(
                "Small dataset (<1000 samples). Collect more data for better generalization."
            )
        
        # Next steps
        recommendations['next_steps'].append(
            "Perform hyperparameter tuning on the best model using GridSearchCV or RandomizedSearchCV"
        )
        recommendations['next_steps'].append(
            "Try ensemble methods (stacking, voting) to combine multiple models"
        )
        recommendations['next_steps'].append(
            "Validate model on unseen production data before deployment"
        )
        
        return recommendations
