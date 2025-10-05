"""
Model Selector
Intelligently selects appropriate ML algorithms based on problem type and dataset characteristics.
"""

from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ModelSelector:
    """
    Selects appropriate machine learning algorithms based on:
    - Problem type (classification/regression)
    - Dataset size
    - Number of features
    - Computational constraints
    """
    
    def __init__(self):
        """Initialize model catalog"""
        self.model_catalog = self._initialize_model_catalog()
    
    def _initialize_model_catalog(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize catalog of available models with metadata.
        
        Returns:
            Dictionary of model configurations
        """
        return {
            # CLASSIFICATION MODELS
            'logistic_regression': {
                'type': 'classification',
                'class': 'sklearn.linear_model.LogisticRegression',
                'params': {
                    'max_iter': 1000,
                    'random_state': 42
                },
                'strengths': ['Fast', 'Interpretable', 'Probabilistic'],
                'weaknesses': ['Linear only', 'Assumes independence'],
                'best_for': 'Linear relationships, binary/multiclass',
                'min_samples': 50,
                'handles_multiclass': True
            },
            'random_forest_classifier': {
                'type': 'classification',
                'class': 'sklearn.ensemble.RandomForestClassifier',
                'params': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'random_state': 42,
                    'n_jobs': -1
                },
                'strengths': ['Non-linear', 'Feature importance', 'Robust to outliers'],
                'weaknesses': ['Slower', 'Black box'],
                'best_for': 'Complex patterns, feature interactions',
                'min_samples': 100,
                'handles_multiclass': True
            },
            'gradient_boosting_classifier': {
                'type': 'classification',
                'class': 'sklearn.ensemble.GradientBoostingClassifier',
                'params': {
                    'n_estimators': 100,
                    'learning_rate': 0.1,
                    'max_depth': 3,
                    'random_state': 42
                },
                'strengths': ['High accuracy', 'Feature importance', 'Handles imbalance'],
                'weaknesses': ['Slower training', 'Overfitting risk'],
                'best_for': 'High accuracy requirements, structured data',
                'min_samples': 100,
                'handles_multiclass': True
            },
            'xgboost_classifier': {
                'type': 'classification',
                'class': 'xgboost.XGBClassifier',
                'params': {
                    'n_estimators': 100,
                    'learning_rate': 0.1,
                    'max_depth': 5,
                    'random_state': 42,
                    'eval_metric': 'logloss',
                    'use_label_encoder': False
                },
                'strengths': ['Best accuracy', 'Fast', 'Regularization'],
                'weaknesses': ['Requires tuning', 'Complex'],
                'best_for': 'Competitions, best performance',
                'min_samples': 100,
                'handles_multiclass': True,
                'requires_package': 'xgboost'
            },
            'decision_tree_classifier': {
                'type': 'classification',
                'class': 'sklearn.tree.DecisionTreeClassifier',
                'params': {
                    'max_depth': 10,
                    'random_state': 42
                },
                'strengths': ['Interpretable', 'Fast', 'No scaling needed'],
                'weaknesses': ['Overfits', 'Unstable'],
                'best_for': 'Baseline, interpretability',
                'min_samples': 50,
                'handles_multiclass': True
            },
            'svm_classifier': {
                'type': 'classification',
                'class': 'sklearn.svm.SVC',
                'params': {
                    'kernel': 'rbf',
                    'probability': True,
                    'random_state': 42
                },
                'strengths': ['Effective in high dimensions', 'Kernel trick'],
                'weaknesses': ['Slow on large datasets', 'Requires scaling'],
                'best_for': 'Small to medium datasets, non-linear boundaries',
                'min_samples': 50,
                'max_samples': 10000,  # Too slow for large datasets
                'handles_multiclass': True
            },
            'naive_bayes': {
                'type': 'classification',
                'class': 'sklearn.naive_bayes.GaussianNB',
                'params': {},
                'strengths': ['Very fast', 'Probabilistic', 'Good for text'],
                'weaknesses': ['Assumes independence', 'Simplistic'],
                'best_for': 'Baseline, text classification, real-time',
                'min_samples': 20,
                'handles_multiclass': True
            },
            'knn_classifier': {
                'type': 'classification',
                'class': 'sklearn.neighbors.KNeighborsClassifier',
                'params': {
                    'n_neighbors': 5,
                    'n_jobs': -1
                },
                'strengths': ['Simple', 'No training', 'Non-parametric'],
                'weaknesses': ['Slow prediction', 'Memory intensive', 'Sensitive to scale'],
                'best_for': 'Small datasets, simple patterns',
                'min_samples': 50,
                'max_samples': 10000,
                'handles_multiclass': True
            },
            
            # REGRESSION MODELS
            'linear_regression': {
                'type': 'regression',
                'class': 'sklearn.linear_model.LinearRegression',
                'params': {},
                'strengths': ['Fast', 'Interpretable', 'Stable'],
                'weaknesses': ['Linear only', 'Sensitive to outliers'],
                'best_for': 'Linear relationships, baseline',
                'min_samples': 50
            },
            'ridge_regression': {
                'type': 'regression',
                'class': 'sklearn.linear_model.Ridge',
                'params': {
                    'alpha': 1.0,
                    'random_state': 42
                },
                'strengths': ['Regularized', 'Handles multicollinearity'],
                'weaknesses': ['Linear only'],
                'best_for': 'Many correlated features',
                'min_samples': 50
            },
            'lasso_regression': {
                'type': 'regression',
                'class': 'sklearn.linear_model.Lasso',
                'params': {
                    'alpha': 1.0,
                    'random_state': 42
                },
                'strengths': ['Feature selection', 'Regularized', 'Sparse solutions'],
                'weaknesses': ['Linear only', 'Can be unstable'],
                'best_for': 'Feature selection, sparse data',
                'min_samples': 50
            },
            'random_forest_regressor': {
                'type': 'regression',
                'class': 'sklearn.ensemble.RandomForestRegressor',
                'params': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'random_state': 42,
                    'n_jobs': -1
                },
                'strengths': ['Non-linear', 'Feature importance', 'Robust'],
                'weaknesses': ['Slower', 'Memory intensive'],
                'best_for': 'Complex patterns, feature interactions',
                'min_samples': 100
            },
            'gradient_boosting_regressor': {
                'type': 'regression',
                'class': 'sklearn.ensemble.GradientBoostingRegressor',
                'params': {
                    'n_estimators': 100,
                    'learning_rate': 0.1,
                    'max_depth': 3,
                    'random_state': 42
                },
                'strengths': ['High accuracy', 'Feature importance'],
                'weaknesses': ['Slower training', 'Overfitting risk'],
                'best_for': 'High accuracy requirements',
                'min_samples': 100
            },
            'xgboost_regressor': {
                'type': 'regression',
                'class': 'xgboost.XGBRegressor',
                'params': {
                    'n_estimators': 100,
                    'learning_rate': 0.1,
                    'max_depth': 5,
                    'random_state': 42
                },
                'strengths': ['Best accuracy', 'Fast', 'Regularization'],
                'weaknesses': ['Requires tuning'],
                'best_for': 'Best performance',
                'min_samples': 100,
                'requires_package': 'xgboost'
            },
            'decision_tree_regressor': {
                'type': 'regression',
                'class': 'sklearn.tree.DecisionTreeRegressor',
                'params': {
                    'max_depth': 10,
                    'random_state': 42
                },
                'strengths': ['Interpretable', 'Fast', 'No scaling needed'],
                'weaknesses': ['Overfits', 'Unstable'],
                'best_for': 'Baseline, interpretability',
                'min_samples': 50
            },
            'svr': {
                'type': 'regression',
                'class': 'sklearn.svm.SVR',
                'params': {
                    'kernel': 'rbf'
                },
                'strengths': ['Effective in high dimensions', 'Robust to outliers'],
                'weaknesses': ['Slow on large datasets', 'Requires scaling'],
                'best_for': 'Small to medium datasets, non-linear',
                'min_samples': 50,
                'max_samples': 10000
            },
            
            # CLUSTERING MODELS
            'kmeans': {
                'type': 'clustering',
                'class': 'sklearn.cluster.KMeans',
                'params': {
                    'n_clusters': 3,
                    'random_state': 42,
                    'n_init': 10
                },
                'strengths': ['Fast', 'Scalable', 'Simple'],
                'weaknesses': ['Requires n_clusters', 'Spherical clusters only', 'Sensitive to outliers'],
                'best_for': 'Well-separated spherical clusters, large datasets',
                'min_samples': 100,
                'requires_n_clusters': True
            },
            'dbscan': {
                'type': 'clustering',
                'class': 'sklearn.cluster.DBSCAN',
                'params': {
                    'eps': 0.5,
                    'min_samples': 5
                },
                'strengths': ['Finds arbitrary shapes', 'No need for n_clusters', 'Detects outliers'],
                'weaknesses': ['Sensitive to parameters', 'Struggles with varying densities'],
                'best_for': 'Arbitrary cluster shapes, noisy data with outliers',
                'min_samples': 50,
                'requires_n_clusters': False
            },
            'hierarchical': {
                'type': 'clustering',
                'class': 'sklearn.cluster.AgglomerativeClustering',
                'params': {
                    'n_clusters': 3,
                    'linkage': 'ward'
                },
                'strengths': ['Dendrograms', 'No random initialization', 'Works with any distance'],
                'weaknesses': ['Slow on large datasets', 'Memory intensive'],
                'best_for': 'Small to medium datasets, hierarchical structure',
                'min_samples': 50,
                'max_samples': 5000,
                'requires_n_clusters': True
            },
            'gaussian_mixture': {
                'type': 'clustering',
                'class': 'sklearn.mixture.GaussianMixture',
                'params': {
                    'n_components': 3,
                    'random_state': 42,
                    'covariance_type': 'full'
                },
                'strengths': ['Soft clustering', 'Flexible shapes', 'Probability estimates'],
                'weaknesses': ['Sensitive to initialization', 'Assumes Gaussian'],
                'best_for': 'Elliptical clusters, probabilistic assignments',
                'min_samples': 100,
                'requires_n_clusters': True
            },
            'spectral': {
                'type': 'clustering',
                'class': 'sklearn.cluster.SpectralClustering',
                'params': {
                    'n_clusters': 3,
                    'random_state': 42,
                    'affinity': 'rbf'
                },
                'strengths': ['Non-convex clusters', 'Graph-based', 'Flexible'],
                'weaknesses': ['Slow', 'Memory intensive', 'No predict method'],
                'best_for': 'Complex cluster shapes, small datasets',
                'min_samples': 50,
                'max_samples': 2000,
                'requires_n_clusters': True
            }
        }
    
    def select_models(
        self,
        problem_type: str,
        n_samples: int,
        n_features: int,
        exclude_slow: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Select appropriate models based on dataset characteristics.
        
        Args:
            problem_type: 'classification' or 'regression'
            n_samples: Number of training samples
            n_features: Number of features
            exclude_slow: Whether to exclude slow models for large datasets
            
        Returns:
            List of model configurations to train
        """
        selected = []
        
        for model_name, config in self.model_catalog.items():
            # Filter by problem type
            if config['type'] != problem_type:
                continue
            
            # Check minimum samples
            if n_samples < config.get('min_samples', 0):
                logger.debug(f"Skipping {model_name}: insufficient samples")
                continue
            
            # Check maximum samples (for slow models)
            if exclude_slow and 'max_samples' in config:
                if n_samples > config['max_samples']:
                    logger.debug(f"Skipping {model_name}: dataset too large")
                    continue
            
            # Check if required package is available
            if 'requires_package' in config:
                try:
                    __import__(config['requires_package'])
                except ImportError:
                    logger.warning(f"Skipping {model_name}: {config['requires_package']} not installed")
                    continue
            
            # Add to selection
            selected.append({
                'name': model_name,
                'config': config
            })
        
        logger.info(f"Selected {len(selected)} models: {[m['name'] for m in selected]}")
        return selected
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        if model_name not in self.model_catalog:
            raise ValueError(f"Unknown model: {model_name}")
        
        return self.model_catalog[model_name]
    
    def recommend_model(
        self,
        problem_type: str,
        n_samples: int,
        n_features: int,
        priority: str = 'accuracy'
    ) -> str:
        """
        Recommend a single best model based on criteria.
        
        Args:
            problem_type: 'classification' or 'regression'
            n_samples: Number of samples
            n_features: Number of features
            priority: 'accuracy', 'speed', or 'interpretability'
            
        Returns:
            Recommended model name
        """
        if priority == 'accuracy':
            if problem_type == 'classification':
                return 'xgboost_classifier' if n_samples >= 100 else 'random_forest_classifier'
            else:
                return 'xgboost_regressor' if n_samples >= 100 else 'random_forest_regressor'
        
        elif priority == 'speed':
            if problem_type == 'classification':
                return 'logistic_regression'
            else:
                return 'linear_regression'
        
        elif priority == 'interpretability':
            if problem_type == 'classification':
                return 'decision_tree_classifier'
            else:
                return 'decision_tree_regressor'
        
        else:
            raise ValueError(f"Unknown priority: {priority}")
