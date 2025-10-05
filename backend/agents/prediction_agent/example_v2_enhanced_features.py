"""
Example: Enhanced Features (v2.0)
Demonstrates all new enterprise-grade capabilities of the Prediction Agent.
"""

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification, make_regression, make_blobs
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_cross_validation():
    """Example 1: Cross-Validation"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Cross-Validation")
    print("="*80)
    
    from cross_validator import CrossValidator
    from sklearn.ensemble import RandomForestClassifier
    
    # Generate data
    X, y = make_classification(n_samples=500, n_features=20, n_classes=2, random_state=42)
    
    # Create model
    model = RandomForestClassifier(random_state=42)
    
    # Cross-validate
    cv = CrossValidator(n_splits=5)
    results = cv.cross_validate_model(
        model=model,
        X=X,
        y=y,
        problem_type='classification',
        scoring=['accuracy', 'f1_weighted', 'roc_auc_ovr_weighted']
    )
    
    print(f"\nCross-Validation Results:")
    print(f"  Accuracy: {results['accuracy']['test_mean']:.4f} ± {results['accuracy']['test_std']:.4f}")
    print(f"  F1 Score: {results['f1_weighted']['test_mean']:.4f} ± {results['f1_weighted']['test_std']:.4f}")
    print(f"  Overfitting Gap: {results['accuracy']['overfitting_gap']:.4f}")


def example_2_hyperparameter_tuning():
    """Example 2: Hyperparameter Tuning"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Hyperparameter Tuning")
    print("="*80)
    
    from hyperparameter_tuner import HyperparameterTuner
    from sklearn.ensemble import RandomForestClassifier
    
    # Generate data
    X, y = make_classification(n_samples=300, n_features=15, n_classes=2, random_state=42)
    
    # Create tuner
    tuner = HyperparameterTuner(cv_folds=3)
    
    # Base model
    model = RandomForestClassifier(random_state=42)
    
    # Tune hyperparameters
    print("\nTuning Random Forest with Random Search...")
    results = tuner.tune_hyperparameters(
        model=model,
        model_name='random_forest_classifier',
        X=X,
        y=y,
        problem_type='classification',
        method='random',
        n_iter=20
    )
    
    print(f"\nBest Parameters: {results['best_params']}")
    print(f"Best CV Score: {results['best_score']:.4f}")
    print(f"Method: {results['method']}")


def example_3_clustering():
    """Example 3: Clustering with Evaluation"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Clustering")
    print("="*80)
    
    from cluster_evaluator import ClusterEvaluator
    from sklearn.cluster import KMeans, DBSCAN
    
    # Generate clustered data
    X, y_true = make_blobs(n_samples=300, centers=4, n_features=2, random_state=42)
    
    # Train models
    kmeans = KMeans(n_clusters=4, random_state=42)
    kmeans.fit(X)
    
    dbscan = DBSCAN(eps=0.8, min_samples=5)
    dbscan.fit(X)
    
    # Evaluate
    evaluator = ClusterEvaluator()
    
    kmeans_metrics = evaluator.evaluate_clustering(kmeans, X, model_name='KMeans')
    dbscan_metrics = evaluator.evaluate_clustering(dbscan, X, model_name='DBSCAN')
    
    print(f"\nKMeans Results:")
    print(f"  Clusters: {kmeans_metrics['n_clusters']}")
    print(f"  Silhouette Score: {kmeans_metrics['silhouette_score']:.4f}")
    print(f"  Davies-Bouldin Index: {kmeans_metrics['davies_bouldin_index']:.4f}")
    
    print(f"\nDBSCAN Results:")
    print(f"  Clusters: {dbscan_metrics['n_clusters']}")
    print(f"  Noise Points: {dbscan_metrics['n_noise_points']}")
    print(f"  Silhouette Score: {dbscan_metrics.get('silhouette_score', 'N/A')}")


def example_4_imbalanced_data():
    """Example 4: Handling Imbalanced Data"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Imbalanced Data Handling")
    print("="*80)
    
    from imbalanced_handler import ImbalancedDataHandler
    
    # Generate imbalanced data
    X, y = make_classification(
        n_samples=1000,
        n_features=10,
        n_classes=2,
        weights=[0.9, 0.1],  # 90-10 imbalance
        random_state=42
    )
    
    handler = ImbalancedDataHandler()
    
    # Detect imbalance
    imbalance_info = handler.detect_imbalance(y)
    
    print(f"\nImbalance Detection:")
    print(f"  Imbalance Ratio: {imbalance_info['imbalance_ratio']:.4f}")
    print(f"  Severity: {imbalance_info['severity']}")
    print(f"  Recommendation: {imbalance_info['recommendation']}")
    print(f"  Class Distribution: {imbalance_info['class_distribution']}")
    
    # Apply SMOTE
    X_resampled, y_resampled, metadata = handler.handle_imbalance(
        X, y, strategy='smote'
    )
    
    print(f"\nAfter SMOTE:")
    print(f"  Original Size: {metadata['original_size']}")
    print(f"  Resampled Size: {metadata['resampled_size']}")
    print(f"  New Distribution: {dict(pd.Series(y_resampled).value_counts())}")


def example_5_ensemble_methods():
    """Example 5: Ensemble Methods"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Ensemble Methods")
    print("="*80)
    
    from ensemble_builder import EnsembleBuilder
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    
    # Generate data
    X, y = make_classification(n_samples=500, n_features=20, n_classes=2, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # Train base models
    models = {
        'rf': RandomForestClassifier(n_estimators=50, random_state=42),
        'gb': GradientBoostingClassifier(n_estimators=50, random_state=42),
        'lr': LogisticRegression(max_iter=1000, random_state=42)
    }
    
    for name, model in models.items():
        model.fit(X_train, y_train)
    
    # Create ensembles
    builder = EnsembleBuilder()
    
    # Voting Ensemble
    voting_ensemble = builder.create_voting_ensemble(
        models=models,
        problem_type='classification',
        voting='soft'
    )
    voting_ensemble.fit(X_train, y_train)
    
    # Stacking Ensemble
    stacking_ensemble, metadata = builder.auto_ensemble(
        trained_models=models,
        X_train=X_train,
        y_train=y_train,
        problem_type='classification',
        ensemble_type='stacking'
    )
    
    # Evaluate
    voting_acc = accuracy_score(y_test, voting_ensemble.predict(X_test))
    stacking_acc = accuracy_score(y_test, stacking_ensemble.predict(X_test))
    
    print(f"\nEnsemble Performance:")
    print(f"  Voting Ensemble: {voting_acc:.4f}")
    print(f"  Stacking Ensemble: {stacking_acc:.4f}")
    print(f"  Stacking Meta-Model: {metadata['meta_model']}")


def example_6_time_series_forecasting():
    """Example 6: Time Series Forecasting"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Time Series Forecasting")
    print("="*80)
    
    from time_series_forecaster import TimeSeriesForecaster
    
    # Generate time series data
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    trend = np.linspace(0, 10, 100)
    seasonal = 5 * np.sin(np.linspace(0, 8*np.pi, 100))
    noise = np.random.normal(0, 1, 100)
    values = trend + seasonal + noise
    
    ts_data = pd.Series(values, index=dates)
    
    # Forecast
    forecaster = TimeSeriesForecaster()
    
    print("\nForecasting next 14 days...")
    result = forecaster.forecast(
        data=ts_data,
        periods=14,
        method='auto',
        seasonal=True
    )
    
    if 'error' not in result:
        print(f"\nForecast Method: {result['method']}")
        print(f"Forecast Values (first 7): {result['forecast'][:7]}")
        if 'aic' in result:
            print(f"AIC: {result['aic']:.2f}")
    else:
        print(f"\nForecasting failed: {result['error']}")
        print("(Install statsmodels or prophet to use this feature)")


def example_7_model_monitoring():
    """Example 7: Model Monitoring & Drift Detection"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Model Monitoring & Drift Detection")
    print("="*80)
    
    from model_monitor import ModelMonitor
    
    # Reference data (training data)
    X_ref, y_ref = make_classification(n_samples=500, n_features=10, random_state=42)
    
    # Current data (production data with drift)
    X_current, y_current = make_classification(
        n_samples=200,
        n_features=10,
        random_state=99,  # Different seed = drift
        flip_y=0.1  # Add noise
    )
    
    # Initialize monitor
    monitor = ModelMonitor(alert_threshold=0.15)
    monitor.set_reference_data(X_ref, y_ref)
    
    # Detect data drift
    print("\nDetecting data drift...")
    drift_results = monitor.detect_data_drift(
        X_current=X_current,
        method='ks'
    )
    
    print(f"\nDrift Detection Results:")
    print(f"  Method: {drift_results['method']}")
    print(f"  Drifted Features: {drift_results['n_drifted_features']}/{len(drift_results['drift_scores'])}")
    print(f"  Drift Percentage: {drift_results['drift_percentage']:.2%}")
    print(f"  Alert: {'⚠️ DRIFT DETECTED' if drift_results['drift_alert'] else '✓ No significant drift'}")
    
    # Track performance (simulated)
    from sklearn.ensemble import RandomForestClassifier
    
    model = RandomForestClassifier(random_state=42)
    model.fit(X_ref, y_ref)
    y_pred = model.predict(X_current)
    
    perf_results = monitor.track_performance(
        y_true=y_current,
        y_pred=y_pred,
        problem_type='classification'
    )
    
    print(f"\nPerformance Tracking:")
    print(f"  Accuracy: {perf_results['accuracy']:.4f}")
    print(f"  F1 Score: {perf_results['f1_score']:.4f}")
    print(f"  Degradation Alert: {perf_results['degradation_alert']}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("PREDICTION AGENT v2.0 - ENHANCED FEATURES DEMONSTRATION")
    print("="*80)
    
    examples = [
        ("Cross-Validation", example_1_cross_validation),
        ("Hyperparameter Tuning", example_2_hyperparameter_tuning),
        ("Clustering", example_3_clustering),
        ("Imbalanced Data", example_4_imbalanced_data),
        ("Ensemble Methods", example_5_ensemble_methods),
        ("Time Series Forecasting", example_6_time_series_forecasting),
        ("Model Monitoring", example_7_model_monitoring),
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ {name} example failed: {str(e)}")
            logger.error(f"{name} example error", exc_info=True)
    
    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED!")
    print("="*80)
    print("\nNext Steps:")
    print("1. Install all dependencies: pip install -r requirements_prediction.txt")
    print("2. Try FastAPI: python -m prediction_agent.api.prediction_api")
    print("3. Integrate with other DataCue agents for complete ML pipeline")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
