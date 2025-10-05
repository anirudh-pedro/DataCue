"""
Ensemble Builder
Creates ensemble models using voting, stacking, and blending techniques.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import VotingClassifier, VotingRegressor, StackingClassifier, StackingRegressor
from sklearn.model_selection import train_test_split
import logging

logger = logging.getLogger(__name__)


class EnsembleBuilder:
    """
    Builds ensemble models to improve prediction accuracy.
    
    Techniques:
    - Voting (soft/hard voting for classification, averaging for regression)
    - Stacking (meta-learner on top of base models)
    - Blending (holdout set for meta-learner)
    """
    
    def __init__(self, random_state: int = 42):
        """
        Initialize ensemble builder.
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
    
    def create_voting_ensemble(
        self,
        models: Dict[str, Any],
        problem_type: str,
        voting: str = 'soft',
        weights: Optional[List[float]] = None
    ) -> Any:
        """
        Create a voting ensemble.
        
        Args:
            models: Dictionary of {name: model_instance}
            problem_type: 'classification' or 'regression'
            voting: 'soft' or 'hard' (classification only)
            weights: Optional weights for each model
            
        Returns:
            Voting ensemble model
        """
        estimators = [(name, model) for name, model in models.items()]
        
        if problem_type == 'classification':
            ensemble = VotingClassifier(
                estimators=estimators,
                voting=voting,
                weights=weights,
                n_jobs=-1
            )
            logger.info(f"   Created VotingClassifier with {len(estimators)} models (voting={voting})")
        else:
            ensemble = VotingRegressor(
                estimators=estimators,
                weights=weights,
                n_jobs=-1
            )
            logger.info(f"   Created VotingRegressor with {len(estimators)} models")
        
        return ensemble
    
    def create_stacking_ensemble(
        self,
        base_models: Dict[str, Any],
        meta_model: Any,
        problem_type: str,
        cv: int = 5
    ) -> Any:
        """
        Create a stacking ensemble.
        
        Args:
            base_models: Dictionary of {name: base_model_instance}
            meta_model: Meta-learner model
            problem_type: 'classification' or 'regression'
            cv: Number of cross-validation folds for stacking
            
        Returns:
            Stacking ensemble model
        """
        estimators = [(name, model) for name, model in base_models.items()]
        
        if problem_type == 'classification':
            ensemble = StackingClassifier(
                estimators=estimators,
                final_estimator=meta_model,
                cv=cv,
                n_jobs=-1,
                passthrough=False
            )
            logger.info(f"   Created StackingClassifier with {len(estimators)} base models")
        else:
            ensemble = StackingRegressor(
                estimators=estimators,
                final_estimator=meta_model,
                cv=cv,
                n_jobs=-1,
                passthrough=False
            )
            logger.info(f"   Created StackingRegressor with {len(estimators)} base models")
        
        return ensemble
    
    def create_blending_ensemble(
        self,
        base_models: Dict[str, Any],
        meta_model: Any,
        X: np.ndarray,
        y: np.ndarray,
        problem_type: str,
        blend_ratio: float = 0.3
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Create a blending ensemble using holdout set.
        
        Args:
            base_models: Dictionary of {name: base_model_instance}
            meta_model: Meta-learner model
            X: Feature matrix
            y: Target vector
            problem_type: 'classification' or 'regression'
            blend_ratio: Ratio of data for meta-model training
            
        Returns:
            Tuple of (ensemble_wrapper, metadata)
        """
        # Split data for blending
        X_base, X_blend, y_base, y_blend = train_test_split(
            X, y,
            test_size=blend_ratio,
            random_state=self.random_state,
            stratify=y if problem_type == 'classification' else None
        )
        
        logger.info(f"   Training base models on {len(X_base)} samples")
        
        # Train base models
        trained_base_models = {}
        blend_predictions = []
        
        for name, model in base_models.items():
            try:
                model.fit(X_base, y_base)
                trained_base_models[name] = model
                
                # Generate predictions on blend set
                if problem_type == 'classification' and hasattr(model, 'predict_proba'):
                    preds = model.predict_proba(X_blend)
                else:
                    preds = model.predict(X_blend).reshape(-1, 1)
                
                blend_predictions.append(preds)
                logger.info(f"      {name} trained")
                
            except Exception as e:
                logger.error(f"      Failed to train {name}: {str(e)}")
        
        # Create meta-features
        if problem_type == 'classification' and all(p.ndim == 2 for p in blend_predictions):
            # Concatenate probability predictions
            X_meta = np.hstack(blend_predictions)
        else:
            # Concatenate predictions
            X_meta = np.column_stack(blend_predictions)
        
        logger.info(f"   Training meta-model on {len(X_blend)} samples with {X_meta.shape[1]} features")
        
        # Train meta-model
        meta_model.fit(X_meta, y_blend)
        
        # Create ensemble wrapper
        ensemble = BlendingEnsemble(
            base_models=trained_base_models,
            meta_model=meta_model,
            problem_type=problem_type
        )
        
        metadata = {
            'n_base_models': len(trained_base_models),
            'base_train_size': len(X_base),
            'blend_size': len(X_blend),
            'meta_features': X_meta.shape[1]
        }
        
        return ensemble, metadata
    
    def auto_ensemble(
        self,
        trained_models: Dict[str, Any],
        X_train: np.ndarray,
        y_train: np.ndarray,
        problem_type: str,
        ensemble_type: str = 'auto',
        top_k: int = 5
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Automatically create best ensemble from trained models.
        
        Args:
            trained_models: Dictionary of trained models
            X_train: Training features
            y_train: Training target
            problem_type: 'classification' or 'regression'
            ensemble_type: 'voting', 'stacking', 'blending', or 'auto'
            top_k: Number of top models to use in ensemble
            
        Returns:
            Tuple of (ensemble_model, metadata)
        """
        # Select top k models (assuming they're already sorted by performance)
        model_names = list(trained_models.keys())[:top_k]
        selected_models = {name: trained_models[name] for name in model_names}
        
        logger.info(f"   Creating {ensemble_type} ensemble with top {len(selected_models)} models")
        
        # Auto-select ensemble type
        if ensemble_type == 'auto':
            # Voting for speed, stacking for accuracy
            ensemble_type = 'voting' if len(X_train) > 10000 else 'stacking'
            logger.info(f"   Auto-selected ensemble type: {ensemble_type}")
        
        # Create ensemble
        if ensemble_type == 'voting':
            ensemble = self.create_voting_ensemble(
                models=selected_models,
                problem_type=problem_type,
                voting='soft' if problem_type == 'classification' else None
            )
            
            # Train ensemble
            ensemble.fit(X_train, y_train)
            
            metadata = {
                'ensemble_type': 'voting',
                'n_models': len(selected_models),
                'model_names': model_names
            }
            
        elif ensemble_type == 'stacking':
            # Select meta-learner
            if problem_type == 'classification':
                from sklearn.linear_model import LogisticRegression
                meta_model = LogisticRegression(max_iter=1000, random_state=self.random_state)
            else:
                from sklearn.linear_model import Ridge
                meta_model = Ridge(random_state=self.random_state)
            
            ensemble = self.create_stacking_ensemble(
                base_models=selected_models,
                meta_model=meta_model,
                problem_type=problem_type,
                cv=5
            )
            
            # Train ensemble
            ensemble.fit(X_train, y_train)
            
            metadata = {
                'ensemble_type': 'stacking',
                'n_base_models': len(selected_models),
                'meta_model': type(meta_model).__name__,
                'model_names': model_names
            }
            
        elif ensemble_type == 'blending':
            # Select meta-learner
            if problem_type == 'classification':
                from sklearn.linear_model import LogisticRegression
                meta_model = LogisticRegression(max_iter=1000, random_state=self.random_state)
            else:
                from sklearn.linear_model import Ridge
                meta_model = Ridge(random_state=self.random_state)
            
            ensemble, blend_meta = self.create_blending_ensemble(
                base_models=selected_models,
                meta_model=meta_model,
                X=X_train,
                y=y_train,
                problem_type=problem_type,
                blend_ratio=0.3
            )
            
            metadata = {
                'ensemble_type': 'blending',
                'meta_model': type(meta_model).__name__,
                'model_names': model_names,
                **blend_meta
            }
            
        else:
            raise ValueError(f"Unknown ensemble type: {ensemble_type}")
        
        return ensemble, metadata
    
    def weighted_voting_optimization(
        self,
        models: Dict[str, Any],
        X_val: np.ndarray,
        y_val: np.ndarray,
        problem_type: str
    ) -> Dict[str, float]:
        """
        Optimize voting weights based on validation performance.
        
        Args:
            models: Dictionary of fitted models
            X_val: Validation features
            y_val: Validation target
            problem_type: 'classification' or 'regression'
            
        Returns:
            Dictionary of optimized weights
        """
        from sklearn.metrics import accuracy_score, r2_score
        
        # Calculate individual model scores
        scores = {}
        for name, model in models.items():
            try:
                y_pred = model.predict(X_val)
                if problem_type == 'classification':
                    score = accuracy_score(y_val, y_pred)
                else:
                    score = r2_score(y_val, y_pred)
                scores[name] = max(score, 0)  # Ensure non-negative
            except Exception as e:
                logger.warning(f"Could not score {name}: {str(e)}")
                scores[name] = 0
        
        # Normalize scores to weights
        total_score = sum(scores.values())
        if total_score > 0:
            weights = {name: score/total_score for name, score in scores.items()}
        else:
            # Equal weights if all failed
            weights = {name: 1.0/len(models) for name in models.keys()}
        
        logger.info(f"   Optimized weights: {weights}")
        return weights


class BlendingEnsemble:
    """
    Wrapper for blending ensemble (manual implementation).
    """
    
    def __init__(
        self,
        base_models: Dict[str, Any],
        meta_model: Any,
        problem_type: str
    ):
        """
        Initialize blending ensemble.
        
        Args:
            base_models: Fitted base models
            meta_model: Fitted meta model
            problem_type: 'classification' or 'regression'
        """
        self.base_models = base_models
        self.meta_model = meta_model
        self.problem_type = problem_type
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        meta_features = self._generate_meta_features(X)
        return self.meta_model.predict(meta_features)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities (classification only)"""
        if self.problem_type != 'classification':
            raise AttributeError("predict_proba only available for classification")
        
        meta_features = self._generate_meta_features(X)
        return self.meta_model.predict_proba(meta_features)
    
    def _generate_meta_features(self, X: np.ndarray) -> np.ndarray:
        """Generate meta-features from base model predictions"""
        predictions = []
        
        for name, model in self.base_models.items():
            if self.problem_type == 'classification' and hasattr(model, 'predict_proba'):
                preds = model.predict_proba(X)
            else:
                preds = model.predict(X).reshape(-1, 1)
            predictions.append(preds)
        
        if self.problem_type == 'classification' and all(p.ndim == 2 for p in predictions):
            return np.hstack(predictions)
        else:
            return np.column_stack(predictions)
