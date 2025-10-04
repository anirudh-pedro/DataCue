"""
Advanced Anomaly Detection & Alert System
Automatically detects unusual patterns and triggers alerts.

Features:
- Multi-method anomaly detection
- Automatic alert generation
- Severity classification
- Alert history tracking
- Anomaly explanations
- Visualization of anomalies
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from scipy import stats


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"      # Immediate action required
    HIGH = "high"              # Action needed soon
    MEDIUM = "medium"          # Monitor closely
    LOW = "low"                # Informational
    INFO = "info"              # No action needed


class AnomalyDetector:
    """
    Advanced anomaly detection with automatic alerts.
    
    Methods:
    - Statistical outlier detection (Z-score, IQR, MAD)
    - Time series anomalies
    - Categorical anomalies
    - Distribution shifts
    - Alert management
    """
    
    def __init__(self, alert_threshold: float = 0.05):
        """
        Initialize anomaly detector.
        
        Args:
            alert_threshold: Threshold for triggering alerts (default: 5%)
        """
        self.alert_threshold = alert_threshold
        self.alerts: List[Dict[str, Any]] = []
        self.anomaly_history: List[Dict[str, Any]] = []
    
    def detect_all_anomalies(
        self,
        data: pd.DataFrame,
        methods: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run all anomaly detection methods.
        
        Args:
            data: DataFrame to analyze
            methods: List of methods to use (default: all)
                Options: 'zscore', 'iqr', 'mad', 'temporal', 'categorical', 'distribution'
            
        Returns:
            Dictionary with all detected anomalies and alerts
        """
        if methods is None:
            methods = ['zscore', 'iqr', 'temporal', 'categorical', 'distribution']
        
        results = {
            'anomalies_by_method': {},
            'total_anomalies': 0,
            'critical_alerts': [],
            'all_alerts': [],
            'summary': {}
        }
        
        # Run each method
        if 'zscore' in methods:
            zscore_anomalies = self.detect_zscore_anomalies(data)
            results['anomalies_by_method']['zscore'] = zscore_anomalies
            results['total_anomalies'] += len(zscore_anomalies['anomalies'])
        
        if 'iqr' in methods:
            iqr_anomalies = self.detect_iqr_anomalies(data)
            results['anomalies_by_method']['iqr'] = iqr_anomalies
            results['total_anomalies'] += len(iqr_anomalies['anomalies'])
        
        if 'temporal' in methods:
            temporal_anomalies = self.detect_temporal_anomalies(data)
            if temporal_anomalies:
                results['anomalies_by_method']['temporal'] = temporal_anomalies
                results['total_anomalies'] += len(temporal_anomalies.get('anomalies', []))
        
        if 'categorical' in methods:
            cat_anomalies = self.detect_categorical_anomalies(data)
            if cat_anomalies:
                results['anomalies_by_method']['categorical'] = cat_anomalies
                results['total_anomalies'] += len(cat_anomalies.get('anomalies', []))
        
        if 'distribution' in methods:
            dist_anomalies = self.detect_distribution_shifts(data)
            if dist_anomalies:
                results['anomalies_by_method']['distribution'] = dist_anomalies
        
        # Generate alerts
        results['all_alerts'] = self.alerts
        results['critical_alerts'] = [a for a in self.alerts if a['severity'] in ['critical', 'high']]
        
        # Summary
        results['summary'] = {
            'total_anomalies': results['total_anomalies'],
            'total_alerts': len(self.alerts),
            'critical_alerts': len(results['critical_alerts']),
            'methods_used': list(results['anomalies_by_method'].keys())
        }
        
        return results
    
    def detect_zscore_anomalies(
        self,
        data: pd.DataFrame,
        threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies using Z-score method.
        
        Args:
            data: DataFrame to analyze
            threshold: Z-score threshold (default: 3.0)
            
        Returns:
            Anomaly detection results
        """
        anomalies = []
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            values = data[col].dropna()
            if len(values) < 3:
                continue
            
            z_scores = np.abs(stats.zscore(values))
            outlier_mask = z_scores > threshold
            n_outliers = outlier_mask.sum()
            
            if n_outliers > 0:
                outlier_pct = n_outliers / len(values)
                severity = self._classify_severity(outlier_pct)
                
                anomaly = {
                    'column': col,
                    'method': 'zscore',
                    'n_anomalies': int(n_outliers),
                    'percentage': round(outlier_pct * 100, 2),
                    'threshold': threshold,
                    'severity': severity.value,
                    'description': f"Found {n_outliers} outliers ({outlier_pct:.1%}) using Z-score > {threshold}",
                    'anomalous_indices': data[data[col].notna()].index[outlier_mask].tolist()[:10]  # Limit to 10
                }
                
                anomalies.append(anomaly)
                
                # Create alert if severe
                if severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                    self._create_alert(
                        alert_type='outlier_zscore',
                        severity=severity,
                        message=f"{col}: {n_outliers} extreme outliers detected (Z-score > {threshold})",
                        details=anomaly
                    )
        
        return {
            'method': 'zscore',
            'threshold': threshold,
            'anomalies': anomalies,
            'total_anomalous_columns': len(anomalies)
        }
    
    def detect_iqr_anomalies(
        self,
        data: pd.DataFrame,
        multiplier: float = 1.5
    ) -> Dict[str, Any]:
        """
        Detect anomalies using IQR (Interquartile Range) method.
        
        Args:
            data: DataFrame to analyze
            multiplier: IQR multiplier (default: 1.5 for standard, 3.0 for extreme)
            
        Returns:
            Anomaly detection results
        """
        anomalies = []
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            values = data[col].dropna()
            if len(values) < 4:
                continue
            
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            
            outlier_mask = (values < lower_bound) | (values > upper_bound)
            n_outliers = outlier_mask.sum()
            
            if n_outliers > 0:
                outlier_pct = n_outliers / len(values)
                severity = self._classify_severity(outlier_pct)
                
                anomaly = {
                    'column': col,
                    'method': 'iqr',
                    'n_anomalies': int(n_outliers),
                    'percentage': round(outlier_pct * 100, 2),
                    'lower_bound': round(lower_bound, 2),
                    'upper_bound': round(upper_bound, 2),
                    'severity': severity.value,
                    'description': f"Found {n_outliers} outliers outside [{lower_bound:.2f}, {upper_bound:.2f}]",
                    'anomalous_indices': data[data[col].notna()].index[outlier_mask].tolist()[:10]
                }
                
                anomalies.append(anomaly)
                
                if severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                    self._create_alert(
                        alert_type='outlier_iqr',
                        severity=severity,
                        message=f"{col}: {n_outliers} outliers outside IQR bounds",
                        details=anomaly
                    )
        
        return {
            'method': 'iqr',
            'multiplier': multiplier,
            'anomalies': anomalies,
            'total_anomalous_columns': len(anomalies)
        }
    
    def detect_temporal_anomalies(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect anomalies in time series data.
        
        Args:
            data: DataFrame with datetime column
            
        Returns:
            Temporal anomaly results or None
        """
        # Find datetime columns
        datetime_cols = data.select_dtypes(include=['datetime64']).columns
        
        if len(datetime_cols) == 0:
            return None
        
        anomalies = []
        
        for date_col in datetime_cols:
            # Check for gaps in time series
            sorted_dates = data[date_col].dropna().sort_values()
            if len(sorted_dates) < 2:
                continue
            
            # Calculate time differences
            diffs = sorted_dates.diff().dropna()
            median_diff = diffs.median()
            
            # Find large gaps (>3x median)
            large_gaps = diffs[diffs > median_diff * 3]
            
            if len(large_gaps) > 0:
                severity = self._classify_severity(len(large_gaps) / len(diffs))
                
                anomaly = {
                    'column': date_col,
                    'method': 'temporal_gaps',
                    'n_anomalies': len(large_gaps),
                    'median_interval': str(median_diff),
                    'largest_gap': str(large_gaps.max()),
                    'severity': severity.value,
                    'description': f"Found {len(large_gaps)} unusually large time gaps"
                }
                
                anomalies.append(anomaly)
                
                if severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                    self._create_alert(
                        alert_type='temporal_gap',
                        severity=severity,
                        message=f"{date_col}: Detected {len(large_gaps)} large time gaps",
                        details=anomaly
                    )
        
        return {
            'method': 'temporal',
            'anomalies': anomalies,
            'total_issues': len(anomalies)
        } if anomalies else None
    
    def detect_categorical_anomalies(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect anomalies in categorical data.
        
        Args:
            data: DataFrame to analyze
            
        Returns:
            Categorical anomaly results or None
        """
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns
        
        if len(categorical_cols) == 0:
            return None
        
        anomalies = []
        
        for col in categorical_cols:
            value_counts = data[col].value_counts()
            total = len(data[col].dropna())
            
            if len(value_counts) < 2:
                continue
            
            # Detect rare categories (<1% or <3 occurrences)
            rare_threshold = max(0.01 * total, 3)
            rare_categories = value_counts[value_counts < rare_threshold]
            
            if len(rare_categories) > 0:
                severity = self._classify_severity(len(rare_categories) / len(value_counts))
                
                anomaly = {
                    'column': col,
                    'method': 'rare_categories',
                    'n_rare_categories': len(rare_categories),
                    'total_categories': len(value_counts),
                    'rare_categories': rare_categories.to_dict(),
                    'severity': severity.value,
                    'description': f"Found {len(rare_categories)} rare categories with <{rare_threshold:.0f} occurrences"
                }
                
                anomalies.append(anomaly)
                
                if len(rare_categories) / len(value_counts) > 0.5:
                    self._create_alert(
                        alert_type='rare_categories',
                        severity=AlertSeverity.MEDIUM,
                        message=f"{col}: {len(rare_categories)} rare categories detected",
                        details=anomaly
                    )
            
            # Detect imbalanced distributions (one category >90%)
            if value_counts.iloc[0] / total > 0.9:
                anomaly = {
                    'column': col,
                    'method': 'imbalanced_categories',
                    'dominant_category': value_counts.index[0],
                    'dominant_percentage': round(value_counts.iloc[0] / total * 100, 1),
                    'severity': AlertSeverity.MEDIUM.value,
                    'description': f"Highly imbalanced: '{value_counts.index[0]}' represents {value_counts.iloc[0]/total:.1%}"
                }
                
                anomalies.append(anomaly)
                
                self._create_alert(
                    alert_type='imbalanced_distribution',
                    severity=AlertSeverity.MEDIUM,
                    message=f"{col}: Highly imbalanced distribution detected",
                    details=anomaly
                )
        
        return {
            'method': 'categorical',
            'anomalies': anomalies,
            'total_issues': len(anomalies)
        } if anomalies else None
    
    def detect_distribution_shifts(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect unusual distributions (highly skewed, heavy-tailed, etc.).
        
        Args:
            data: DataFrame to analyze
            
        Returns:
            Distribution anomaly results or None
        """
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        anomalies = []
        
        for col in numeric_cols:
            values = data[col].dropna()
            if len(values) < 10:
                continue
            
            # Calculate distribution statistics
            skewness = values.skew()
            kurtosis = values.kurtosis()
            
            # Check for extreme skewness (|skew| > 2)
            if abs(skewness) > 2:
                severity = AlertSeverity.MEDIUM if abs(skewness) > 3 else AlertSeverity.LOW
                
                anomaly = {
                    'column': col,
                    'issue': 'high_skewness',
                    'skewness': round(skewness, 2),
                    'severity': severity.value,
                    'description': f"Highly skewed distribution (skew={skewness:.2f})",
                    'recommendation': 'Consider log transformation or removal of outliers'
                }
                
                anomalies.append(anomaly)
            
            # Check for heavy tails (kurtosis > 7)
            if kurtosis > 7:
                severity = AlertSeverity.MEDIUM if kurtosis > 10 else AlertSeverity.LOW
                
                anomaly = {
                    'column': col,
                    'issue': 'heavy_tails',
                    'kurtosis': round(kurtosis, 2),
                    'severity': severity.value,
                    'description': f"Heavy-tailed distribution (kurtosis={kurtosis:.2f})",
                    'recommendation': 'Investigate extreme values'
                }
                
                anomalies.append(anomaly)
        
        return {
            'method': 'distribution_analysis',
            'anomalies': anomalies,
            'total_issues': len(anomalies)
        } if anomalies else None
    
    def _classify_severity(self, anomaly_percentage: float) -> AlertSeverity:
        """
        Classify severity based on anomaly percentage.
        
        Args:
            anomaly_percentage: Percentage of anomalous data (0-1)
            
        Returns:
            AlertSeverity enum
        """
        if anomaly_percentage > 0.2:  # >20%
            return AlertSeverity.CRITICAL
        elif anomaly_percentage > 0.1:  # >10%
            return AlertSeverity.HIGH
        elif anomaly_percentage > 0.05:  # >5%
            return AlertSeverity.MEDIUM
        elif anomaly_percentage > 0.01:  # >1%
            return AlertSeverity.LOW
        else:
            return AlertSeverity.INFO
    
    def _create_alert(
        self,
        alert_type: str,
        severity: AlertSeverity,
        message: str,
        details: Dict[str, Any]
    ) -> None:
        """Create and store an alert."""
        alert = {
            'id': len(self.alerts) + 1,
            'type': alert_type,
            'severity': severity.value,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False
        }
        
        self.alerts.append(alert)
    
    def get_critical_alerts(self) -> List[Dict[str, Any]]:
        """Get all critical and high severity alerts."""
        return [a for a in self.alerts if a['severity'] in ['critical', 'high']]
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """
        Mark an alert as acknowledged.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if acknowledged, False if not found
        """
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
                return True
        return False
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all alerts."""
        severity_counts = {}
        for alert in self.alerts:
            sev = alert['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        return {
            'total_alerts': len(self.alerts),
            'by_severity': severity_counts,
            'unacknowledged': sum(1 for a in self.alerts if not a.get('acknowledged', False)),
            'critical_count': severity_counts.get('critical', 0),
            'high_count': severity_counts.get('high', 0)
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AnomalyDetector("
            f"alerts={len(self.alerts)}, "
            f"critical={len(self.get_critical_alerts())})"
        )
