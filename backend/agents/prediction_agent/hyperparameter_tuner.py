"""
Hyperparameter Tuner
Performs automated hyperparameter optimization using GridSearch, RandomSearch, and Optuna.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
import logging

logger = logging.getLogger(__name__)


class HyperparameterTuner:
    """
    Automates hyperparameter tuning for machine learning models.
    
    Features:
    - GridSearchCV for exhaustive search
    - RandomizedSearchCV for faster search
    - Optuna for Bayesian optimization (optional)
    - Predefined search spaces for common algorithms
    """
    
    def __init__(
        self,
        cv_folds: int = 5,
        n_jobs: int = -1,
        random_state: int = 42,
        verbose: int = 1
    ):
        """
        Initialize hyperparameter tuner.
        
        Args:
            cv_folds: Number of cross-validation folds
            n_jobs: Number of parallel jobs (-1 = all cores)
            random_state: Random seed for reproducibility
            verbose: Verbosity level
        """
        self.cv_folds = cv_folds
        self.n_jobs = n_jobs
        self.random_state = random_state
        self.verbose = verbose
        self.optuna_available = self._check_optuna()
    
    def _check_optuna(self) -> bool:
        """Check if Optuna is available"""
        try:
            import optuna
            return True
        except ImportError:
            logger.info("Optuna not installed. Using GridSearch/RandomSearch only.")
            return False
    
    def tune_hyperparameters(
        self,
        model,
        model_name: str,
        X: np.ndarray,
        y: np.ndarray,
        problem_type: str,
        method: str = 'random',
        n_iter: int = 50,
        param_space: Optional[Dict] = None,
        scoring: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tune hyperparameters for a model.
        
        Args:
            model: Base model instance
            model_name: Name of the model (for lookup)
            X: Feature matrix
            y: Target vector
            problem_type: 'classification' or 'regression'
            method: 'grid', 'random', or 'optuna'
            n_iter: Number of iterations for RandomSearch/Optuna
            param_space: Custom parameter space (optional)
            scoring: Scoring metric (auto-detected if None)
            
        Returns:
            Dictionary with best parameters, best score, and tuned model
        """
        logger.info(f"   Tuning hyperparameters for {model_name} using {method} search...")
        
        # Get parameter space
        if param_space is None:
            param_space = self._get_param_space(model_name, method)
        
        if not param_space:
            logger.warning(f"   No parameter space defined for {model_name}")
            return {
                'best_params': {},
                'best_score': None,
                'tuned_model': model,
                'method': method
            }
        
        # Get scoring metric
        if scoring is None:
            scoring = 'accuracy' if problem_type == 'classification' else 'r2'
        
        # Perform tuning based on method
        if method == 'grid':
            return self._grid_search(model, X, y, param_space, scoring)
        elif method == 'random':
            return self._random_search(model, X, y, param_space, scoring, n_iter)
        elif method == 'optuna' and self.optuna_available:
            return self._optuna_search(model, model_name, X, y, param_space, scoring, n_iter)
        else:
            logger.warning(f"Method '{method}' not available, falling back to random search")
            return self._random_search(model, X, y, param_space, scoring, n_iter)
    
    def _grid_search(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: Dict,
        scoring: str
    ) -> Dict[str, Any]:
        """
        Perform GridSearchCV.
        """
        try:
            grid_search = GridSearchCV(
                estimator=model,
                param_grid=param_grid,
                cv=self.cv_folds,
                scoring=scoring,
                n_jobs=self.n_jobs,
                verbose=self.verbose,
                return_train_score=True
            )
            
            grid_search.fit(X, y)
            
            return {
                'best_params': grid_search.best_params_,
                'best_score': float(grid_search.best_score_),
                'tuned_model': grid_search.best_estimator_,
                'method': 'grid',
                'cv_results': self._extract_cv_results(grid_search.cv_results_),
                'n_trials': len(grid_search.cv_results_['params'])
            }
            
        except Exception as e:
            logger.error(f"   Grid search failed: {str(e)}")
            return {'error': str(e)}
    
    def _random_search(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        param_distributions: Dict,
        scoring: str,
        n_iter: int
    ) -> Dict[str, Any]:
        """
        Perform RandomizedSearchCV.
        """
        try:
            random_search = RandomizedSearchCV(
                estimator=model,
                param_distributions=param_distributions,
                n_iter=n_iter,
                cv=self.cv_folds,
                scoring=scoring,
                n_jobs=self.n_jobs,
                verbose=self.verbose,
                random_state=self.random_state,
                return_train_score=True
            )
            
            random_search.fit(X, y)
            
            return {
                'best_params': random_search.best_params_,
                'best_score': float(random_search.best_score_),
                'tuned_model': random_search.best_estimator_,
                'method': 'random',
                'cv_results': self._extract_cv_results(random_search.cv_results_),
                'n_trials': n_iter
            }
            
        except Exception as e:
            logger.error(f"   Random search failed: {str(e)}")
            return {'error': str(e)}
    
    def _optuna_search(
        self,
        model,
        model_name: str,
        X: np.ndarray,
        y: np.ndarray,
        param_space: Dict,
        scoring: str,
        n_trials: int
    ) -> Dict[str, Any]:
        """
        Perform Optuna Bayesian optimization.
        """
        try:
            import optuna
            from sklearn.model_selection import cross_val_score
            
            def objective(trial):
                # Sample parameters based on space
                params = {}
                for param_name, param_config in param_space.items():
                    if isinstance(param_config, dict) and 'type' in param_config:
                        if param_config['type'] == 'int':
                            params[param_name] = trial.suggest_int(
                                param_name,
                                param_config['low'],
                                param_config['high']
                            )
                        elif param_config['type'] == 'float':
                            params[param_name] = trial.suggest_float(
                                param_name,
                                param_config['low'],
                                param_config['high'],
                                log=param_config.get('log', False)
                            )
                        elif param_config['type'] == 'categorical':
                            params[param_name] = trial.suggest_categorical(
                                param_name,
                                param_config['choices']
                            )
                    else:
                        # Fall back to categorical for simple lists
                        params[param_name] = trial.suggest_categorical(param_name, param_config)
                
                # Create model with parameters
                model_instance = model.__class__(**params)
                
                # Cross-validate
                scores = cross_val_score(
                    model_instance, X, y,
                    cv=self.cv_folds,
                    scoring=scoring,
                    n_jobs=self.n_jobs
                )
                
                return scores.mean()
            
            # Create study
            study = optuna.create_study(
                direction='maximize',
                sampler=optuna.samplers.TPESampler(seed=self.random_state)
            )
            
            # Optimize
            study.optimize(objective, n_trials=n_trials, n_jobs=1)
            
            # Train final model with best params
            best_model = model.__class__(**study.best_params)
            best_model.fit(X, y)
            
            return {
                'best_params': study.best_params,
                'best_score': float(study.best_value),
                'tuned_model': best_model,
                'method': 'optuna',
                'n_trials': n_trials,
                'optimization_history': [
                    {'trial': i, 'value': trial.value}
                    for i, trial in enumerate(study.trials)
                ]
            }
            
        except Exception as e:
            logger.error(f"   Optuna search failed: {str(e)}")
            return {'error': str(e)}
    
    def _get_param_space(self, model_name: str, method: str) -> Dict[str, Any]:
        """
        Get predefined parameter space for common models.
        
        Returns different spaces for grid vs random/optuna search.
        """
        # Define parameter spaces for all models
        param_spaces = {
            # CLASSIFICATION MODELS
            'logistic_regression': {
                'grid': {
                    'C': [0.01, 0.1, 1.0, 10.0],
                    'penalty': ['l2'],
                    'solver': ['lbfgs', 'liblinear']
                },
                'random': {
                    'C': {'type': 'float', 'low': 0.001, 'high': 100.0, 'log': True},
                    'penalty': ['l1', 'l2'],
                    'solver': ['lbfgs', 'liblinear', 'saga']
                }
            },
            'random_forest_classifier': {
                'grid': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 20, None],
                    'min_samples_split': [2, 5, 10]
                },
                'random': {
                    'n_estimators': {'type': 'int', 'low': 50, 'high': 500},
                    'max_depth': [5, 10, 20, 30, None],
                    'min_samples_split': {'type': 'int', 'low': 2, 'high': 20},
                    'min_samples_leaf': {'type': 'int', 'low': 1, 'high': 10},
                    'max_features': ['sqrt', 'log2', None]
                }
            },
            'gradient_boosting_classifier': {
                'grid': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.3],
                    'max_depth': [3, 5, 7]
                },
                'random': {
                    'n_estimators': {'type': 'int', 'low': 50, 'high': 500},
                    'learning_rate': {'type': 'float', 'low': 0.001, 'high': 0.5, 'log': True},
                    'max_depth': {'type': 'int', 'low': 3, 'high': 10},
                    'subsample': {'type': 'float', 'low': 0.6, 'high': 1.0}
                }
            },
            'xgboost_classifier': {
                'grid': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.3],
                    'max_depth': [3, 5, 7],
                    'subsample': [0.8, 1.0]
                },
                'random': {
                    'n_estimators': {'type': 'int', 'low': 50, 'high': 500},
                    'learning_rate': {'type': 'float', 'low': 0.001, 'high': 0.3, 'log': True},
                    'max_depth': {'type': 'int', 'low': 3, 'high': 10},
                    'min_child_weight': {'type': 'int', 'low': 1, 'high': 10},
                    'subsample': {'type': 'float', 'low': 0.6, 'high': 1.0},
                    'colsample_bytree': {'type': 'float', 'low': 0.6, 'high': 1.0},
                    'gamma': {'type': 'float', 'low': 0, 'high': 5}
                }
            },
            'decision_tree_classifier': {
                'grid': {
                    'max_depth': [3, 5, 10, None],
                    'min_samples_split': [2, 5, 10],
                    'criterion': ['gini', 'entropy']
                },
                'random': {
                    'max_depth': [3, 5, 10, 20, None],
                    'min_samples_split': {'type': 'int', 'low': 2, 'high': 20},
                    'min_samples_leaf': {'type': 'int', 'low': 1, 'high': 10},
                    'criterion': ['gini', 'entropy']
                }
            },
            'svm_classifier': {
                'grid': {
                    'C': [0.1, 1.0, 10.0],
                    'kernel': ['linear', 'rbf'],
                    'gamma': ['scale', 'auto']
                },
                'random': {
                    'C': {'type': 'float', 'low': 0.01, 'high': 100.0, 'log': True},
                    'kernel': ['linear', 'rbf', 'poly'],
                    'gamma': ['scale', 'auto']
                }
            },
            'knn_classifier': {
                'grid': {
                    'n_neighbors': [3, 5, 7, 11],
                    'weights': ['uniform', 'distance'],
                    'metric': ['euclidean', 'manhattan']
                },
                'random': {
                    'n_neighbors': {'type': 'int', 'low': 3, 'high': 20},
                    'weights': ['uniform', 'distance'],
                    'metric': ['euclidean', 'manhattan', 'minkowski']
                }
            },
            
            # REGRESSION MODELS
            'linear_regression': {
                'grid': {},  # No hyperparameters to tune
                'random': {}
            },
            'ridge_regression': {
                'grid': {
                    'alpha': [0.1, 1.0, 10.0, 100.0]
                },
                'random': {
                    'alpha': {'type': 'float', 'low': 0.01, 'high': 1000.0, 'log': True}
                }
            },
            'lasso_regression': {
                'grid': {
                    'alpha': [0.1, 1.0, 10.0, 100.0]
                },
                'random': {
                    'alpha': {'type': 'float', 'low': 0.01, 'high': 1000.0, 'log': True}
                }
            },
            'random_forest_regressor': {
                'grid': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 20, None],
                    'min_samples_split': [2, 5, 10]
                },
                'random': {
                    'n_estimators': {'type': 'int', 'low': 50, 'high': 500},
                    'max_depth': [5, 10, 20, 30, None],
                    'min_samples_split': {'type': 'int', 'low': 2, 'high': 20},
                    'min_samples_leaf': {'type': 'int', 'low': 1, 'high': 10},
                    'max_features': ['sqrt', 'log2', None]
                }
            },
            'gradient_boosting_regressor': {
                'grid': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.3],
                    'max_depth': [3, 5, 7]
                },
                'random': {
                    'n_estimators': {'type': 'int', 'low': 50, 'high': 500},
                    'learning_rate': {'type': 'float', 'low': 0.001, 'high': 0.5, 'log': True},
                    'max_depth': {'type': 'int', 'low': 3, 'high': 10},
                    'subsample': {'type': 'float', 'low': 0.6, 'high': 1.0}
                }
            },
            'xgboost_regressor': {
                'grid': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.3],
                    'max_depth': [3, 5, 7],
                    'subsample': [0.8, 1.0]
                },
                'random': {
                    'n_estimators': {'type': 'int', 'low': 50, 'high': 500},
                    'learning_rate': {'type': 'float', 'low': 0.001, 'high': 0.3, 'log': True},
                    'max_depth': {'type': 'int', 'low': 3, 'high': 10},
                    'min_child_weight': {'type': 'int', 'low': 1, 'high': 10},
                    'subsample': {'type': 'float', 'low': 0.6, 'high': 1.0},
                    'colsample_bytree': {'type': 'float', 'low': 0.6, 'high': 1.0},
                    'gamma': {'type': 'float', 'low': 0, 'high': 5}
                }
            },
            'decision_tree_regressor': {
                'grid': {
                    'max_depth': [3, 5, 10, None],
                    'min_samples_split': [2, 5, 10]
                },
                'random': {
                    'max_depth': [3, 5, 10, 20, None],
                    'min_samples_split': {'type': 'int', 'low': 2, 'high': 20},
                    'min_samples_leaf': {'type': 'int', 'low': 1, 'high': 10}
                }
            },
            'svr_regressor': {
                'grid': {
                    'C': [0.1, 1.0, 10.0],
                    'kernel': ['linear', 'rbf'],
                    'gamma': ['scale', 'auto']
                },
                'random': {
                    'C': {'type': 'float', 'low': 0.01, 'high': 100.0, 'log': True},
                    'kernel': ['linear', 'rbf', 'poly'],
                    'gamma': ['scale', 'auto'],
                    'epsilon': {'type': 'float', 'low': 0.01, 'high': 1.0}
                }
            }
        }
        
        # Get appropriate space
        if model_name in param_spaces:
            search_type = 'grid' if method == 'grid' else 'random'
            return param_spaces[model_name].get(search_type, {})
        
        return {}
    
    def _extract_cv_results(self, cv_results: Dict) -> Dict[str, Any]:
        """
        Extract key results from CV results.
        """
        return {
            'mean_test_score': cv_results['mean_test_score'].tolist()[:10],  # Top 10
            'std_test_score': cv_results['std_test_score'].tolist()[:10],
            'params': cv_results['params'][:10]
        }
