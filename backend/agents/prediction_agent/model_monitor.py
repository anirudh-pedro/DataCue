"""
Model Monitor
Monitors model performance and detects data drift in production.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModelMonitor:
    """
    Monitors ML models in production for:
    - Performance degradation
    - Data drift
    - Prediction drift
    - Alert generation
    """
    
    def __init__(self, alert_threshold: float = 0.1):
        """
        Initialize model monitor.
        
        Args:
            alert_threshold: Threshold for triggering alerts
        """
        self.alert_threshold = alert_threshold
        self.reference_data = None
        self.reference_predictions = None
        self.performance_history = []
    
    def set_reference_data(
        self,
        X_reference: np.ndarray,
        y_reference: Optional[np.ndarray] = None,
        predictions_reference: Optional[np.ndarray] = None
    ):
        """
        Set reference (training/validation) data for drift detection.
        
        Args:
            X_reference: Reference feature data
            y_reference: Reference labels (optional)
            predictions_reference: Reference predictions (optional)
        """
        self.reference_data = X_reference
        self.reference_labels = y_reference
        self.reference_predictions = predictions_reference
        
        logger.info(f"Reference data set: {X_reference.shape[0]} samples, {X_reference.shape[1]} features")
    
    def detect_data_drift(
        self,
        X_current: np.ndarray,
        method: str = 'auto',
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect data drift between reference and current data.
        
        Args:
            X_current: Current production data
            method: 'ks' (Kolmogorov-Smirnov), 'psi' (Population Stability Index), or 'auto'
            feature_names: Optional feature names
            
        Returns:
            Dictionary with drift detection results
        """
        if self.reference_data is None:
            raise ValueError("Reference data not set. Call set_reference_data() first.")
        
        logger.info(f"Detecting data drift using {method} method")
        
        n_features = X_current.shape[1]
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(n_features)]
        
        drift_scores = {}
        drift_detected = []
        
        for i, feature_name in enumerate(feature_names):
            if i >= X_current.shape[1] or i >= self.reference_data.shape[1]:
                continue
            
            reference_feature = self.reference_data[:, i]
            current_feature = X_current[:, i]
            
            # Compute drift score
            if method == 'ks' or method == 'auto':
                score = self._kolmogorov_smirnov_test(reference_feature, current_feature)
                threshold = 0.05  # p-value threshold
            elif method == 'psi':
                score = self._population_stability_index(reference_feature, current_feature)
                threshold = 0.2  # PSI threshold
            else:
                raise ValueError(f"Unknown method: {method}")
            
            drift_scores[feature_name] = float(score)
            
            # Check if drift detected
            if method == 'ks':
                if score < threshold:  # Low p-value = drift
                    drift_detected.append(feature_name)
            else:  # PSI
                if score > threshold:  # High PSI = drift
                    drift_detected.append(feature_name)
        
        overall_drift = len(drift_detected) / len(feature_names) if feature_names else 0
        
        return {
            'method': method,
            'drift_scores': drift_scores,
            'drifted_features': drift_detected,
            'n_drifted_features': len(drift_detected),
            'drift_percentage': float(overall_drift),
            'drift_alert': overall_drift > self.alert_threshold,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_prediction_drift(
        self,
        predictions_current: np.ndarray,
        problem_type: str = 'classification'
    ) -> Dict[str, Any]:
        """
        Detect drift in prediction distribution.
        
        Args:
            predictions_current: Current predictions
            problem_type: 'classification' or 'regression'
            
        Returns:
            Dictionary with prediction drift results
        """
        if self.reference_predictions is None:
            logger.warning("Reference predictions not set. Skipping prediction drift detection.")
            return {'error': 'No reference predictions'}
        
        if problem_type == 'classification':
            # Compare class distributions
            ref_dist = np.bincount(self.reference_predictions.astype(int))
            curr_dist = np.bincount(predictions_current.astype(int))
            
            # Pad to same length
            max_len = max(len(ref_dist), len(curr_dist))
            ref_dist = np.pad(ref_dist, (0, max_len - len(ref_dist)))
            curr_dist = np.pad(curr_dist, (0, max_len - len(curr_dist)))
            
            # Normalize
            ref_dist = ref_dist / ref_dist.sum()
            curr_dist = curr_dist / curr_dist.sum()
            
            # Calculate drift (KL divergence)
            drift_score = self._kl_divergence(ref_dist, curr_dist)
            
        else:  # regression
            # Compare distributions using KS test
            from scipy.stats import ks_2samp
            statistic, p_value = ks_2samp(self.reference_predictions, predictions_current)
            drift_score = float(statistic)
        
        return {
            'drift_score': float(drift_score),
            'drift_alert': drift_score > self.alert_threshold,
            'problem_type': problem_type,
            'timestamp': datetime.now().isoformat()
        }
    
    def track_performance(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        problem_type: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Track model performance over time.
        
        Args:
            y_true: True labels
            y_pred: Predictions
            problem_type: 'classification' or 'regression'
            timestamp: Optional timestamp
            
        Returns:
            Performance metrics with alert status
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Calculate metrics
        if problem_type == 'classification':
            from sklearn.metrics import accuracy_score, f1_score
            accuracy = accuracy_score(y_true, y_pred)
            f1 = f1_score(y_true, y_pred, average='weighted')
            metrics = {'accuracy': float(accuracy), 'f1_score': float(f1)}
        else:
            from sklearn.metrics import r2_score, mean_absolute_error
            r2 = r2_score(y_true, y_pred)
            mae = mean_absolute_error(y_true, y_pred)
            metrics = {'r2_score': float(r2), 'mae': float(mae)}
        
        # Store in history
        record = {
            'timestamp': timestamp.isoformat(),
            'metrics': metrics,
            'n_samples': len(y_true)
        }
        self.performance_history.append(record)
        
        # Check for degradation
        degradation_detected = self._detect_performance_degradation(metrics, problem_type)
        
        return {
            **metrics,
            'degradation_alert': degradation_detected,
            'timestamp': timestamp.isoformat()
        }
    
    def _kolmogorov_smirnov_test(
        self,
        reference: np.ndarray,
        current: np.ndarray
    ) -> float:
        """Perform Kolmogorov-Smirnov test"""
        from scipy.stats import ks_2samp
        
        # Remove NaN values
        reference = reference[~np.isnan(reference)]
        current = current[~np.isnan(current)]
        
        if len(reference) == 0 or len(current) == 0:
            return 1.0
        
        statistic, p_value = ks_2samp(reference, current)
        return float(p_value)
    
    def _population_stability_index(
        self,
        reference: np.ndarray,
        current: np.ndarray,
        bins: int = 10
    ) -> float:
        """Calculate Population Stability Index (PSI)"""
        # Remove NaN values
        reference = reference[~np.isnan(reference)]
        current = current[~np.isnan(current)]
        
        if len(reference) == 0 or len(current) == 0:
            return 0.0
        
        # Create bins based on reference data
        bin_edges = np.percentile(reference, np.linspace(0, 100, bins + 1))
        bin_edges = np.unique(bin_edges)  # Remove duplicates
        
        if len(bin_edges) < 2:
            return 0.0
        
        # Calculate distributions
        ref_counts, _ = np.histogram(reference, bins=bin_edges)
        curr_counts, _ = np.histogram(current, bins=bin_edges)
        
        # Normalize to percentages
        ref_pct = ref_counts / len(reference)
        curr_pct = curr_counts / len(current)
        
        # Avoid division by zero
        ref_pct = np.where(ref_pct == 0, 0.0001, ref_pct)
        curr_pct = np.where(curr_pct == 0, 0.0001, curr_pct)
        
        # Calculate PSI
        psi = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
        
        return float(psi)
    
    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """Calculate Kullback-Leibler divergence"""
        # Avoid log(0)
        p = np.where(p == 0, 1e-10, p)
        q = np.where(q == 0, 1e-10, q)
        
        return float(np.sum(p * np.log(p / q)))
    
    def _detect_performance_degradation(
        self,
        current_metrics: Dict[str, float],
        problem_type: str
    ) -> bool:
        """Detect if performance has degraded significantly"""
        if len(self.performance_history) < 2:
            return False
        
        # Get baseline (average of first few records)
        baseline_records = self.performance_history[:min(5, len(self.performance_history))]
        
        if problem_type == 'classification':
            baseline_score = np.mean([r['metrics']['accuracy'] for r in baseline_records])
            current_score = current_metrics['accuracy']
        else:
            baseline_score = np.mean([r['metrics']['r2_score'] for r in baseline_records])
            current_score = current_metrics['r2_score']
        
        # Check for significant drop
        degradation = (baseline_score - current_score) / (baseline_score + 1e-10)
        
        return degradation > self.alert_threshold
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        if not self.performance_history:
            return {'error': 'No performance history available'}
        
        # Calculate summary statistics
        recent_records = self.performance_history[-10:]
        
        report = {
            'total_predictions': len(self.performance_history),
            'recent_performance': recent_records,
            'alerts': {
                'total_alerts': sum(1 for r in recent_records if r.get('degradation_alert', False))
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return report
