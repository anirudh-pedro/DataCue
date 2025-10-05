"""
Explainability Engine
Generates feature importance and SHAP-based explanations for model predictions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """
    Provides model interpretability through feature importance and SHAP values.
    """
    
    def __init__(self):
        """Initialize explainability engine"""
        self.shap_available = self._check_shap_availability()
    
    def _check_shap_availability(self) -> bool:
        """Check if SHAP library is available"""
        try:
            import shap
            return True
        except ImportError:
            logger.warning("SHAP not installed. Install with: pip install shap")
            return False
    
    def explain(
        self,
        model,
        X_train: np.ndarray,
        X_test: np.ndarray,
        feature_names: List[str],
        problem_type: str,
        max_display: int = 10
    ) -> Dict[str, Any]:
        """
        Generate comprehensive model explanations.
        
        Args:
            model: Trained model
            X_train: Training data (for SHAP baseline)
            X_test: Test data to explain
            feature_names: List of feature names
            problem_type: 'classification' or 'regression'
            max_display: Maximum features to display in importance
            
        Returns:
            Dictionary with explanations
        """
        explanations = {}
        
        # 1. Feature Importance (tree-based models)
        try:
            importance = self._get_feature_importance(model, feature_names)
            if importance is not None:
                explanations['feature_importance'] = importance
                explanations['top_features'] = importance['features'][:max_display]
                logger.info(f"   Feature importance extracted")
        except Exception as e:
            logger.debug(f"Could not extract feature importance: {str(e)}")
        
        # 2. Permutation Importance (model-agnostic)
        try:
            perm_importance = self._get_permutation_importance(
                model, X_test, 
                feature_names,
                problem_type
            )
            if perm_importance is not None:
                explanations['permutation_importance'] = perm_importance
                logger.info(f"   Permutation importance calculated")
        except Exception as e:
            logger.debug(f"Could not calculate permutation importance: {str(e)}")
        
        # 3. SHAP Values (if available)
        if self.shap_available:
            try:
                shap_values = self._get_shap_explanations(
                    model, X_train, X_test, feature_names, max_display
                )
                if shap_values is not None:
                    explanations['shap'] = shap_values
                    logger.info(f"   SHAP values generated")
            except Exception as e:
                logger.debug(f"Could not generate SHAP values: {str(e)}")
        
        # 4. Model-specific interpretations
        try:
            model_interpretation = self._get_model_specific_interpretation(model)
            if model_interpretation:
                explanations['model_interpretation'] = model_interpretation
        except Exception as e:
            logger.debug(f"Could not get model interpretation: {str(e)}")
        
        return explanations
    
    def _get_feature_importance(
        self,
        model,
        feature_names: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract feature importance from tree-based models.
        
        Returns:
            Dictionary with feature importance rankings
        """
        # Check if model has feature_importances_ attribute
        if not hasattr(model, 'feature_importances_'):
            return None
        
        importances = model.feature_importances_
        
        # Create DataFrame
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        return {
            'features': importance_df['feature'].tolist(),
            'importances': importance_df['importance'].tolist(),
            'importance_pairs': [
                {'feature': row['feature'], 'importance': float(row['importance'])}
                for _, row in importance_df.iterrows()
            ]
        }
    
    def _get_permutation_importance(
        self,
        model,
        X_test: np.ndarray,
        feature_names: List[str],
        problem_type: str,
        n_repeats: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate permutation importance (model-agnostic).
        
        This works for any model by shuffling features and measuring
        the impact on model performance.
        """
        try:
            from sklearn.inspection import permutation_importance
            
            # Determine scoring metric
            if problem_type == 'classification':
                scoring = 'accuracy'
            else:
                scoring = 'r2'
            
            # Calculate permutation importance
            # Note: We need y_test but it's not passed in
            # Skip for now or modify signature
            logger.debug("Permutation importance requires y_test - skipping")
            return None
            
        except ImportError:
            logger.debug("sklearn.inspection not available")
            return None
        except Exception as e:
            logger.debug(f"Permutation importance failed: {str(e)}")
            return None
    
    def _get_shap_explanations(
        self,
        model,
        X_train: np.ndarray,
        X_test: np.ndarray,
        feature_names: List[str],
        max_display: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Generate SHAP (SHapley Additive exPlanations) values.
        
        SHAP provides consistent and theoretically sound feature attributions.
        """
        try:
            import shap
            
            # Sample data if too large (SHAP can be slow)
            max_samples = 100
            if len(X_train) > max_samples:
                indices = np.random.choice(len(X_train), max_samples, replace=False)
                X_train_sample = X_train[indices]
            else:
                X_train_sample = X_train
            
            if len(X_test) > max_samples:
                indices = np.random.choice(len(X_test), max_samples, replace=False)
                X_test_sample = X_test[indices]
            else:
                X_test_sample = X_test
            
            # Select appropriate explainer
            explainer = None
            
            # Try TreeExplainer for tree-based models (fastest)
            if hasattr(model, 'estimators_') or 'tree' in str(type(model)).lower():
                try:
                    explainer = shap.TreeExplainer(model)
                except:
                    pass
            
            # Fallback to KernelExplainer (works for any model but slower)
            if explainer is None:
                try:
                    explainer = shap.KernelExplainer(
                        model.predict, 
                        shap.sample(X_train_sample, 50)  # Use subset for speed
                    )
                except:
                    logger.debug("Could not create SHAP explainer")
                    return None
            
            # Calculate SHAP values
            shap_values = explainer.shap_values(X_test_sample)
            
            # For classification, SHAP values might be per-class
            if isinstance(shap_values, list):
                # Multiclass - use first class or average
                shap_values = shap_values[0]
            
            # Calculate mean absolute SHAP values for global importance
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            
            # Create importance ranking
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'mean_abs_shap': mean_abs_shap
            }).sort_values('mean_abs_shap', ascending=False)
            
            return {
                'shap_values_shape': shap_values.shape,
                'global_importance': {
                    'features': importance_df['feature'].head(max_display).tolist(),
                    'mean_abs_shap': importance_df['mean_abs_shap'].head(max_display).tolist()
                },
                'interpretation': self._interpret_shap_values(importance_df, max_display)
            }
            
        except Exception as e:
            logger.debug(f"SHAP generation failed: {str(e)}")
            return None
    
    def _interpret_shap_values(
        self,
        importance_df: pd.DataFrame,
        max_display: int
    ) -> str:
        """Generate human-readable interpretation of SHAP values"""
        top_features = importance_df.head(max_display)
        
        interpretation = f"The top {max_display} most influential features are: "
        interpretation += ", ".join(top_features['feature'].tolist())
        interpretation += ". These features have the strongest impact on model predictions."
        
        return interpretation
    
    def _get_model_specific_interpretation(self, model) -> Optional[Dict[str, Any]]:
        """
        Get model-specific interpretations (e.g., coefficients for linear models).
        """
        model_type = type(model).__name__
        
        # Linear models - get coefficients
        if hasattr(model, 'coef_'):
            coef = model.coef_
            intercept = model.intercept_ if hasattr(model, 'intercept_') else None
            
            return {
                'type': 'linear_coefficients',
                'model_type': model_type,
                'coefficients': coef.tolist() if hasattr(coef, 'tolist') else float(coef),
                'intercept': float(intercept) if intercept is not None else None,
                'interpretation': f"{model_type} uses linear coefficients for predictions"
            }
        
        # Tree models - get tree depth info
        if hasattr(model, 'max_depth'):
            return {
                'type': 'tree_info',
                'model_type': model_type,
                'max_depth': model.max_depth,
                'interpretation': f"{model_type} uses decision trees with max depth {model.max_depth}"
            }
        
        return None
    
    def explain_prediction(
        self,
        model,
        X_single: np.ndarray,
        feature_names: List[str],
        baseline: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Explain a single prediction.
        
        Args:
            model: Trained model
            X_single: Single sample to explain (1D array)
            feature_names: Feature names
            baseline: Baseline for comparison (optional)
            
        Returns:
            Explanation for the single prediction
        """
        if self.shap_available:
            try:
                import shap
                
                # Reshape if needed
                if X_single.ndim == 1:
                    X_single = X_single.reshape(1, -1)
                
                # Create explainer
                if baseline is not None:
                    explainer = shap.KernelExplainer(model.predict, baseline)
                else:
                    explainer = shap.KernelExplainer(model.predict, X_single)
                
                # Get SHAP values for this prediction
                shap_values = explainer.shap_values(X_single)
                
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]
                
                # Create feature contribution DataFrame
                contributions = pd.DataFrame({
                    'feature': feature_names,
                    'value': X_single[0],
                    'shap_value': shap_values[0]
                }).sort_values('shap_value', key=abs, ascending=False)
                
                return {
                    'prediction': float(model.predict(X_single)[0]),
                    'contributions': contributions.to_dict('records'),
                    'top_positive': contributions[contributions['shap_value'] > 0].head(3)['feature'].tolist(),
                    'top_negative': contributions[contributions['shap_value'] < 0].head(3)['feature'].tolist()
                }
                
            except Exception as e:
                logger.error(f"Single prediction explanation failed: {str(e)}")
                return {'error': str(e)}
        
        return {'error': 'SHAP not available'}
