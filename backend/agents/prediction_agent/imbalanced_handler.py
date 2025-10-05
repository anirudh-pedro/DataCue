"""
Imbalanced Data Handler
Handles class imbalance in classification tasks using various techniques.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class ImbalancedDataHandler:
    """
    Handles imbalanced datasets using:
    - SMOTE (Synthetic Minority Over-sampling Technique)
    - ADASYN (Adaptive Synthetic Sampling)
    - Random Over/Under Sampling
    - Class weighting
    
    Features:
    - Automatic imbalance detection
    - Strategy recommendation
    - Safe application (validates data quality)
    """
    
    def __init__(self):
        """Initialize imbalanced data handler"""
        self.imblearn_available = self._check_imblearn()
    
    def _check_imblearn(self) -> bool:
        """Check if imbalanced-learn is available"""
        try:
            import imblearn
            return True
        except ImportError:
            logger.warning("imbalanced-learn not installed. Install with: pip install imbalanced-learn")
            return False
    
    def detect_imbalance(
        self,
        y: np.ndarray,
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Detect class imbalance in target variable.
        
        Args:
            y: Target variable
            threshold: Imbalance ratio threshold (minority/majority)
            
        Returns:
            Dictionary with imbalance statistics
        """
        # Count classes
        class_counts = Counter(y)
        total = len(y)
        
        # Calculate ratios
        class_ratios = {cls: count/total for cls, count in class_counts.items()}
        
        # Find minority and majority classes
        sorted_classes = sorted(class_counts.items(), key=lambda x: x[1])
        minority_class, minority_count = sorted_classes[0]
        majority_class, majority_count = sorted_classes[-1]
        
        # Imbalance ratio
        imbalance_ratio = minority_count / majority_count
        
        # Determine severity
        if imbalance_ratio >= 0.8:
            severity = 'balanced'
            recommendation = 'No action needed'
        elif imbalance_ratio >= threshold:
            severity = 'mild_imbalance'
            recommendation = 'Consider class weighting or light resampling'
        elif imbalance_ratio >= 0.1:
            severity = 'moderate_imbalance'
            recommendation = 'Apply SMOTE or class weighting'
        else:
            severity = 'severe_imbalance'
            recommendation = 'Combine SMOTE with class weighting, or use specialized algorithms'
        
        return {
            'is_imbalanced': imbalance_ratio < threshold,
            'imbalance_ratio': float(imbalance_ratio),
            'severity': severity,
            'class_distribution': dict(class_counts),
            'class_ratios': {str(k): float(v) for k, v in class_ratios.items()},
            'minority_class': int(minority_class),
            'majority_class': int(majority_class),
            'recommendation': recommendation
        }
    
    def handle_imbalance(
        self,
        X: np.ndarray,
        y: np.ndarray,
        strategy: str = 'auto',
        sampling_strategy: str = 'auto'
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Apply imbalance handling technique.
        
        Args:
            X: Feature matrix
            y: Target vector
            strategy: 'smote', 'adasyn', 'oversample', 'undersample', 'class_weight', or 'auto'
            sampling_strategy: Sampling ratio or 'auto'
            
        Returns:
            Tuple of (X_resampled, y_resampled, metadata)
        """
        # Detect imbalance
        imbalance_info = self.detect_imbalance(y)
        
        # Auto-select strategy
        if strategy == 'auto':
            strategy = self._select_strategy(imbalance_info)
        
        logger.info(f"   Handling imbalance using: {strategy}")
        
        # Apply strategy
        if strategy == 'smote':
            return self._apply_smote(X, y, sampling_strategy, imbalance_info)
        elif strategy == 'adasyn':
            return self._apply_adasyn(X, y, sampling_strategy, imbalance_info)
        elif strategy == 'oversample':
            return self._apply_random_oversample(X, y, sampling_strategy, imbalance_info)
        elif strategy == 'undersample':
            return self._apply_random_undersample(X, y, sampling_strategy, imbalance_info)
        elif strategy == 'class_weight':
            return self._apply_class_weight(X, y, imbalance_info)
        elif strategy == 'none':
            logger.info("   No resampling applied")
            return X, y, {'strategy': 'none', **imbalance_info}
        else:
            logger.warning(f"Unknown strategy: {strategy}, using SMOTE")
            return self._apply_smote(X, y, sampling_strategy, imbalance_info)
    
    def _select_strategy(self, imbalance_info: Dict[str, Any]) -> str:
        """
        Auto-select best strategy based on imbalance severity.
        """
        severity = imbalance_info['severity']
        
        if severity == 'balanced':
            return 'none'
        elif severity == 'mild_imbalance':
            return 'class_weight'
        elif severity == 'moderate_imbalance':
            return 'smote' if self.imblearn_available else 'class_weight'
        else:  # severe_imbalance
            return 'smote' if self.imblearn_available else 'oversample'
    
    def _apply_smote(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sampling_strategy: str,
        imbalance_info: Dict
    ) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Apply SMOTE (Synthetic Minority Over-sampling)"""
        if not self.imblearn_available:
            logger.warning("imbalanced-learn not available, falling back to random oversampling")
            return self._apply_random_oversample(X, y, sampling_strategy, imbalance_info)
        
        try:
            from imblearn.over_sampling import SMOTE
            
            # Determine k_neighbors based on minority class size
            minority_count = imbalance_info['class_distribution'][imbalance_info['minority_class']]
            k_neighbors = min(5, minority_count - 1) if minority_count > 1 else 1
            
            smote = SMOTE(
                sampling_strategy=sampling_strategy,
                k_neighbors=k_neighbors,
                random_state=42
            )
            
            X_resampled, y_resampled = smote.fit_resample(X, y)
            
            logger.info(f"   SMOTE applied: {len(y)} -> {len(y_resampled)} samples")
            
            return X_resampled, y_resampled, {
                'strategy': 'smote',
                'original_size': len(y),
                'resampled_size': len(y_resampled),
                **imbalance_info
            }
            
        except Exception as e:
            logger.error(f"   SMOTE failed: {str(e)}")
            return self._apply_random_oversample(X, y, sampling_strategy, imbalance_info)
    
    def _apply_adasyn(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sampling_strategy: str,
        imbalance_info: Dict
    ) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Apply ADASYN (Adaptive Synthetic Sampling)"""
        if not self.imblearn_available:
            logger.warning("imbalanced-learn not available, falling back to SMOTE")
            return self._apply_smote(X, y, sampling_strategy, imbalance_info)
        
        try:
            from imblearn.over_sampling import ADASYN
            
            minority_count = imbalance_info['class_distribution'][imbalance_info['minority_class']]
            n_neighbors = min(5, minority_count - 1) if minority_count > 1 else 1
            
            adasyn = ADASYN(
                sampling_strategy=sampling_strategy,
                n_neighbors=n_neighbors,
                random_state=42
            )
            
            X_resampled, y_resampled = adasyn.fit_resample(X, y)
            
            logger.info(f"   ADASYN applied: {len(y)} -> {len(y_resampled)} samples")
            
            return X_resampled, y_resampled, {
                'strategy': 'adasyn',
                'original_size': len(y),
                'resampled_size': len(y_resampled),
                **imbalance_info
            }
            
        except Exception as e:
            logger.error(f"   ADASYN failed: {str(e)}, falling back to SMOTE")
            return self._apply_smote(X, y, sampling_strategy, imbalance_info)
    
    def _apply_random_oversample(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sampling_strategy: str,
        imbalance_info: Dict
    ) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Apply random oversampling"""
        if not self.imblearn_available:
            # Manual random oversampling
            from collections import Counter
            
            class_counts = Counter(y)
            max_count = max(class_counts.values())
            
            X_list = []
            y_list = []
            
            for cls, count in class_counts.items():
                mask = y == cls
                X_cls = X[mask]
                y_cls = y[mask]
                
                # Oversample minority classes
                if count < max_count:
                    n_samples = max_count - count
                    indices = np.random.choice(len(X_cls), size=n_samples, replace=True)
                    X_list.append(X_cls)
                    X_list.append(X_cls[indices])
                    y_list.append(y_cls)
                    y_list.append(y_cls[indices])
                else:
                    X_list.append(X_cls)
                    y_list.append(y_cls)
            
            X_resampled = np.vstack(X_list)
            y_resampled = np.hstack(y_list)
        else:
            from imblearn.over_sampling import RandomOverSampler
            
            ros = RandomOverSampler(
                sampling_strategy=sampling_strategy,
                random_state=42
            )
            X_resampled, y_resampled = ros.fit_resample(X, y)
        
        logger.info(f"   Random oversampling applied: {len(y)} -> {len(y_resampled)} samples")
        
        return X_resampled, y_resampled, {
            'strategy': 'random_oversample',
            'original_size': len(y),
            'resampled_size': len(y_resampled),
            **imbalance_info
        }
    
    def _apply_random_undersample(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sampling_strategy: str,
        imbalance_info: Dict
    ) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Apply random undersampling"""
        if not self.imblearn_available:
            from collections import Counter
            
            class_counts = Counter(y)
            min_count = min(class_counts.values())
            
            X_list = []
            y_list = []
            
            for cls in class_counts.keys():
                mask = y == cls
                X_cls = X[mask]
                y_cls = y[mask]
                
                # Undersample to match minority class
                indices = np.random.choice(len(X_cls), size=min_count, replace=False)
                X_list.append(X_cls[indices])
                y_list.append(y_cls[indices])
            
            X_resampled = np.vstack(X_list)
            y_resampled = np.hstack(y_list)
        else:
            from imblearn.under_sampling import RandomUnderSampler
            
            rus = RandomUnderSampler(
                sampling_strategy=sampling_strategy,
                random_state=42
            )
            X_resampled, y_resampled = rus.fit_resample(X, y)
        
        logger.info(f"   Random undersampling applied: {len(y)} -> {len(y_resampled)} samples")
        
        return X_resampled, y_resampled, {
            'strategy': 'random_undersample',
            'original_size': len(y),
            'resampled_size': len(y_resampled),
            **imbalance_info
        }
    
    def _apply_class_weight(
        self,
        X: np.ndarray,
        y: np.ndarray,
        imbalance_info: Dict
    ) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Calculate class weights (doesn't resample data).
        Returns original data with class weight information.
        """
        from sklearn.utils.class_weight import compute_class_weight
        
        classes = np.unique(y)
        class_weights = compute_class_weight('balanced', classes=classes, y=y)
        class_weight_dict = {cls: weight for cls, weight in zip(classes, class_weights)}
        
        logger.info(f"   Class weights calculated: {class_weight_dict}")
        
        return X, y, {
            'strategy': 'class_weight',
            'class_weights': {int(k): float(v) for k, v in class_weight_dict.items()},
            'use_class_weight': True,
            **imbalance_info
        }
    
    def get_class_weights(self, y: np.ndarray) -> Dict[int, float]:
        """
        Get class weights for use in model training.
        
        Args:
            y: Target vector
            
        Returns:
            Dictionary mapping class labels to weights
        """
        from sklearn.utils.class_weight import compute_class_weight
        
        classes = np.unique(y)
        class_weights = compute_class_weight('balanced', classes=classes, y=y)
        return {int(cls): float(weight) for cls, weight in zip(classes, class_weights)}
