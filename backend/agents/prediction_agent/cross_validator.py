"""
Cross Validator
Implements k-fold cross-validation for robust model evaluation and performance estimation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.model_selection import (
    cross_val_score, cross_validate,
    KFold, StratifiedKFold, TimeSeriesSplit,
    cross_val_predict
)
from sklearn.metrics import make_scorer, get_scorer
import logging

logger = logging.getLogger(__name__)


class CrossValidator:
    """
    Performs cross-validation to estimate model performance and reduce overfitting.
    
    Features:
    - K-Fold and Stratified K-Fold for classification
    - Time Series Split for temporal data
    - Multiple scoring metrics
    - Cross-validated predictions
    """
    
    def __init__(
        self,
        n_splits: int = 5,
        shuffle: bool = True,
        random_state: int = 42
    ):
        """
        Initialize cross-validator.
        
        Args:
            n_splits: Number of folds
            shuffle: Whether to shuffle data before splitting
            random_state: Random seed for reproducibility
        """
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state
    
    def cross_validate_model(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        problem_type: str,
        cv_strategy: str = 'auto',
        scoring: Optional[List[str]] = None,
        return_predictions: bool = False
    ) -> Dict[str, Any]:
        """
        Perform cross-validation on a single model.
        
        Args:
            model: Scikit-learn compatible model
            X: Feature matrix
            y: Target vector
            problem_type: 'classification', 'regression', or 'timeseries'
            cv_strategy: 'kfold', 'stratified', 'timeseries', or 'auto'
            scoring: List of scoring metrics to compute
            return_predictions: Whether to return cross-validated predictions
            
        Returns:
            Dictionary with CV results
        """
        # Select CV strategy
        cv = self._get_cv_splitter(problem_type, cv_strategy, y)
        
        # Default scoring metrics
        if scoring is None:
            scoring = self._get_default_scoring(problem_type)
        
        # Perform cross-validation
        logger.info(f"   Running {self.n_splits}-fold cross-validation...")
        
        try:
            # Cross validate with multiple metrics
            cv_results = cross_validate(
                model, X, y,
                cv=cv,
                scoring=scoring,
                return_train_score=True,
                n_jobs=-1,
                error_score='raise'
            )
            
            # Calculate statistics
            results = self._compute_cv_statistics(cv_results, scoring)
            
            # Get cross-validated predictions if requested
            if return_predictions:
                try:
                    y_pred_cv = cross_val_predict(model, X, y, cv=cv, n_jobs=-1)
                    results['cv_predictions'] = y_pred_cv
                except Exception as e:
                    logger.warning(f"Could not generate CV predictions: {str(e)}")
            
            # Add metadata
            results['n_splits'] = self.n_splits
            results['cv_strategy'] = cv_strategy if cv_strategy != 'auto' else self._detect_cv_strategy(problem_type, y)
            
            logger.info(f"   ✓ Cross-validation complete")
            return results
            
        except Exception as e:
            logger.error(f"   Cross-validation failed: {str(e)}")
            return {'error': str(e)}
    
    def cross_validate_multiple_models(
        self,
        models: Dict[str, Any],
        X: np.ndarray,
        y: np.ndarray,
        problem_type: str,
        cv_strategy: str = 'auto',
        scoring: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Cross-validate multiple models and compare performance.
        
        Args:
            models: Dictionary of {model_name: model_instance}
            X: Feature matrix
            y: Target vector
            problem_type: 'classification', 'regression', or 'timeseries'
            cv_strategy: CV splitting strategy
            scoring: List of scoring metrics
            
        Returns:
            Dictionary with CV results for each model
        """
        all_results = {}
        
        for model_name, model in models.items():
            logger.info(f"Cross-validating {model_name}...")
            
            results = self.cross_validate_model(
                model=model,
                X=X,
                y=y,
                problem_type=problem_type,
                cv_strategy=cv_strategy,
                scoring=scoring,
                return_predictions=False
            )
            
            all_results[model_name] = results
        
        # Create comparison DataFrame
        comparison_df = self._create_cv_comparison(all_results, scoring)
        
        return {
            'individual_results': all_results,
            'comparison_df': comparison_df,
            'best_model': self._identify_best_cv_model(all_results, problem_type)
        }
    
    def _get_cv_splitter(self, problem_type: str, cv_strategy: str, y: np.ndarray):
        """
        Get appropriate CV splitter based on problem type and strategy.
        """
        if cv_strategy == 'auto':
            cv_strategy = self._detect_cv_strategy(problem_type, y)
        
        if cv_strategy == 'stratified':
            return StratifiedKFold(
                n_splits=self.n_splits,
                shuffle=self.shuffle,
                random_state=self.random_state
            )
        elif cv_strategy == 'timeseries':
            return TimeSeriesSplit(n_splits=self.n_splits)
        else:  # 'kfold'
            return KFold(
                n_splits=self.n_splits,
                shuffle=self.shuffle,
                random_state=self.random_state
            )
    
    def _detect_cv_strategy(self, problem_type: str, y: np.ndarray) -> str:
        """
        Automatically detect best CV strategy.
        """
        if problem_type == 'timeseries':
            return 'timeseries'
        elif problem_type == 'classification':
            # Use stratified for classification to preserve class distribution
            return 'stratified'
        else:
            return 'kfold'
    
    def _get_default_scoring(self, problem_type: str) -> List[str]:
        """
        Get default scoring metrics based on problem type.
        """
        if problem_type == 'classification':
            return ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted', 'roc_auc_ovr_weighted']
        else:  # regression
            return ['r2', 'neg_mean_squared_error', 'neg_mean_absolute_error']
    
    def _compute_cv_statistics(
        self,
        cv_results: Dict[str, np.ndarray],
        scoring: List[str]
    ) -> Dict[str, Any]:
        """
        Compute statistics from cross-validation results.
        """
        results = {}
        
        # Process each metric
        for metric in scoring:
            test_key = f'test_{metric}'
            train_key = f'train_{metric}'
            
            if test_key in cv_results:
                test_scores = cv_results[test_key]
                train_scores = cv_results[train_key]
                
                # Handle negative scores (sklearn convention for minimization)
                if metric.startswith('neg_'):
                    test_scores = -test_scores
                    train_scores = -train_scores
                    metric_name = metric.replace('neg_', '')
                else:
                    metric_name = metric
                
                results[metric_name] = {
                    'test_mean': float(np.mean(test_scores)),
                    'test_std': float(np.std(test_scores)),
                    'test_min': float(np.min(test_scores)),
                    'test_max': float(np.max(test_scores)),
                    'train_mean': float(np.mean(train_scores)),
                    'train_std': float(np.std(train_scores)),
                    'overfitting_gap': float(np.mean(train_scores) - np.mean(test_scores)),
                    'all_fold_scores': test_scores.tolist()
                }
        
        # Fit time
        if 'fit_time' in cv_results:
            results['fit_time'] = {
                'mean': float(np.mean(cv_results['fit_time'])),
                'std': float(np.std(cv_results['fit_time']))
            }
        
        return results
    
    def _create_cv_comparison(
        self,
        all_results: Dict[str, Dict[str, Any]],
        scoring: List[str]
    ) -> pd.DataFrame:
        """
        Create comparison DataFrame from CV results.
        """
        comparison_data = []
        
        for model_name, results in all_results.items():
            if 'error' in results:
                continue
            
            row = {'model': model_name}
            
            # Get primary metric (first in scoring list)
            if scoring and len(scoring) > 0:
                primary_metric = scoring[0].replace('neg_', '')
                if primary_metric in results:
                    row['cv_score_mean'] = results[primary_metric]['test_mean']
                    row['cv_score_std'] = results[primary_metric]['test_std']
                    row['overfitting_gap'] = results[primary_metric]['overfitting_gap']
            
            # Add all metrics
            for metric_name, metric_data in results.items():
                if isinstance(metric_data, dict) and 'test_mean' in metric_data:
                    row[f'{metric_name}_mean'] = metric_data['test_mean']
                    row[f'{metric_name}_std'] = metric_data['test_std']
            
            comparison_data.append(row)
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            # Sort by primary score descending
            if 'cv_score_mean' in df.columns:
                df = df.sort_values('cv_score_mean', ascending=False)
            return df
        else:
            return pd.DataFrame()
    
    def _identify_best_cv_model(
        self,
        all_results: Dict[str, Dict[str, Any]],
        problem_type: str
    ) -> Dict[str, Any]:
        """
        Identify best model based on CV scores.
        """
        best_model = None
        best_score = -np.inf
        
        # Determine primary metric
        primary_metric = 'accuracy' if problem_type == 'classification' else 'r2'
        
        for model_name, results in all_results.items():
            if 'error' in results:
                continue
            
            if primary_metric in results:
                score = results[primary_metric]['test_mean']
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        return {
            'model_name': best_model,
            'cv_score': float(best_score),
            'metric': primary_metric
        }
    
    def learning_curve_analysis(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        problem_type: str,
        train_sizes: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Analyze learning curves to detect over/underfitting.
        
        Args:
            model: Model to analyze
            X: Feature matrix
            y: Target vector
            problem_type: 'classification' or 'regression'
            train_sizes: Array of training set sizes to evaluate
            
        Returns:
            Dictionary with learning curve data
        """
        from sklearn.model_selection import learning_curve
        
        if train_sizes is None:
            train_sizes = np.linspace(0.1, 1.0, 10)
        
        cv = self._get_cv_splitter(problem_type, 'auto', y)
        scoring = 'accuracy' if problem_type == 'classification' else 'r2'
        
        try:
            train_sizes_abs, train_scores, test_scores = learning_curve(
                model, X, y,
                cv=cv,
                train_sizes=train_sizes,
                scoring=scoring,
                n_jobs=-1,
                random_state=self.random_state
            )
            
            return {
                'train_sizes': train_sizes_abs.tolist(),
                'train_scores_mean': np.mean(train_scores, axis=1).tolist(),
                'train_scores_std': np.std(train_scores, axis=1).tolist(),
                'test_scores_mean': np.mean(test_scores, axis=1).tolist(),
                'test_scores_std': np.std(test_scores, axis=1).tolist(),
                'convergence': self._assess_convergence(train_scores, test_scores)
            }
        except Exception as e:
            logger.error(f"Learning curve analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _assess_convergence(
        self,
        train_scores: np.ndarray,
        test_scores: np.ndarray
    ) -> Dict[str, Any]:
        """
        Assess if learning curves have converged.
        """
        train_mean = np.mean(train_scores, axis=1)
        test_mean = np.mean(test_scores, axis=1)
        
        # Check if test score is still improving
        recent_improvement = test_mean[-1] - test_mean[-3] if len(test_mean) >= 3 else 0
        
        # Check gap between train and test
        final_gap = train_mean[-1] - test_mean[-1]
        
        return {
            'has_converged': recent_improvement < 0.01,
            'final_gap': float(final_gap),
            'needs_more_data': recent_improvement > 0.02,
            'overfitting_detected': final_gap > 0.15
        }
