"""
Data Preprocessor
Handles data preprocessing including train/test split, encoding, and scaling.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
import logging

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Preprocesses data for machine learning:
    - Train/test split
    - Categorical encoding
    - Numerical scaling
    - Missing value handling
    """
    
    def __init__(self):
        """Initialize preprocessor"""
        self.scaler = None
        self.encoders = {}
        self.feature_names = []
    
    def preprocess(
        self,
        data: pd.DataFrame,
        target_column: str,
        problem_type: str,
        test_size: float = 0.2,
        random_state: int = 42,
        scale_features: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Complete preprocessing pipeline.
        
        Args:
            data: Input DataFrame
            target_column: Name of target variable
            problem_type: 'classification' or 'regression'
            test_size: Proportion for test set
            random_state: Random seed
            scale_features: Whether to scale numerical features
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test, preprocessing_info)
        """
        # Separate features and target
        X = data.drop(columns=[target_column])
        y = data[target_column]
        
        # Handle target encoding for classification
        target_encoder = None
        if problem_type == 'classification':
            if y.dtype == 'object' or y.dtype.name == 'category':
                target_encoder = LabelEncoder()
                y = target_encoder.fit_transform(y)
                logger.info(f"   Target encoded: {len(target_encoder.classes_)} classes")
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y if problem_type == 'classification' else None
        )
        
        # Identify column types
        numeric_features = X_train.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_features = X_train.select_dtypes(include=['object', 'category']).columns.tolist()
        
        logger.info(f"   Numeric features: {len(numeric_features)}, Categorical: {len(categorical_features)}")
        
        # Process categorical features
        if categorical_features:
            X_train, X_test, cat_info = self._encode_categorical(
                X_train, X_test, categorical_features
            )
        else:
            cat_info = {}
        
        # Process numeric features
        if scale_features and numeric_features:
            X_train, X_test, scaling_info = self._scale_numeric(
                X_train, X_test, numeric_features
            )
        else:
            scaling_info = {'scaled': False}
        
        # Convert to numpy arrays
        X_train_array = X_train.values if isinstance(X_train, pd.DataFrame) else X_train
        X_test_array = X_test.values if isinstance(X_test, pd.DataFrame) else X_test
        y_train_array = y_train.values if isinstance(y_train, pd.Series) else y_train
        y_test_array = y_test.values if isinstance(y_test, pd.Series) else y_test
        
        # Store feature names
        self.feature_names = X_train.columns.tolist() if isinstance(X_train, pd.DataFrame) else [f"feature_{i}" for i in range(X_train_array.shape[1])]
        
        # Preprocessing info for later use
        preprocessing_info = {
            'feature_names': self.feature_names,
            'numeric_features': numeric_features,
            'categorical_features': categorical_features,
            'categorical_info': cat_info,
            'scaling_info': scaling_info,
            'target_encoder': target_encoder,
            'target_classes': target_encoder.classes_.tolist() if target_encoder else None,
            'test_size': test_size,
            'random_state': random_state
        }
        
        return X_train_array, X_test_array, y_train_array, y_test_array, preprocessing_info
    
    def _encode_categorical(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        categorical_features: List[str]
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Encode categorical features using one-hot encoding.
        
        Returns:
            Tuple of (X_train_encoded, X_test_encoded, encoding_info)
        """
        encoders = {}
        cat_info = {
            'method': 'one_hot',
            'features': categorical_features,
            'cardinalities': {}
        }
        
        X_train_encoded = X_train.copy()
        X_test_encoded = X_test.copy()
        
        for col in categorical_features:
            # Get unique values and cardinality
            unique_vals = X_train[col].nunique()
            cat_info['cardinalities'][col] = unique_vals
            
            # Use one-hot encoding for low cardinality
            if unique_vals <= 10:
                # One-hot encode
                train_dummies = pd.get_dummies(X_train[col], prefix=col, drop_first=True)
                test_dummies = pd.get_dummies(X_test[col], prefix=col, drop_first=True)
                
                # Align columns (test might not have all categories)
                test_dummies = test_dummies.reindex(columns=train_dummies.columns, fill_value=0)
                
                # Drop original and add dummies
                X_train_encoded = X_train_encoded.drop(columns=[col])
                X_test_encoded = X_test_encoded.drop(columns=[col])
                
                X_train_encoded = pd.concat([X_train_encoded, train_dummies], axis=1)
                X_test_encoded = pd.concat([X_test_encoded, test_dummies], axis=1)
                
                encoders[col] = {
                    'type': 'one_hot',
                    'columns': train_dummies.columns.tolist()
                }
            else:
                # High cardinality - use label encoding
                le = LabelEncoder()
                X_train_encoded[col] = le.fit_transform(X_train[col].astype(str))
                # Handle unseen categories in test
                X_test_encoded[col] = X_test[col].apply(
                    lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else -1
                )
                
                encoders[col] = {
                    'type': 'label',
                    'encoder': le,
                    'classes': le.classes_.tolist()
                }
        
        cat_info['encoders'] = encoders
        
        return X_train_encoded, X_test_encoded, cat_info
    
    def _scale_numeric(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        numeric_features: List[str]
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Scale numeric features using StandardScaler.
        
        Returns:
            Tuple of (X_train_scaled, X_test_scaled, scaling_info)
        """
        self.scaler = StandardScaler()
        
        X_train_copy = X_train.copy()
        X_test_copy = X_test.copy()
        
        # Fit on train, transform both
        X_train_copy[numeric_features] = self.scaler.fit_transform(X_train[numeric_features])
        X_test_copy[numeric_features] = self.scaler.transform(X_test[numeric_features])
        
        scaling_info = {
            'scaled': True,
            'method': 'StandardScaler',
            'features': numeric_features,
            'mean': self.scaler.mean_.tolist(),
            'std': self.scaler.scale_.tolist()
        }
        
        return X_train_copy, X_test_copy, scaling_info
    
    def preprocess_new_data(
        self,
        data: pd.DataFrame,
        preprocessor_info: Dict[str, Any]
    ) -> np.ndarray:
        """
        Preprocess new data using fitted preprocessors.
        
        Args:
            data: New DataFrame to preprocess
            preprocessor_info: Info from original preprocessing
            
        Returns:
            Preprocessed numpy array
        """
        X = data.copy()
        
        # Handle categorical features
        cat_info = preprocessor_info.get('categorical_info', {})
        if cat_info and 'encoders' in cat_info:
            for col, encoder_info in cat_info['encoders'].items():
                if col not in X.columns:
                    continue
                
                if encoder_info['type'] == 'one_hot':
                    # Apply one-hot encoding
                    dummies = pd.get_dummies(X[col], prefix=col, drop_first=True)
                    # Align with training columns
                    dummies = dummies.reindex(columns=encoder_info['columns'], fill_value=0)
                    X = X.drop(columns=[col])
                    X = pd.concat([X, dummies], axis=1)
                else:
                    # Label encoding
                    le = encoder_info['encoder']
                    X[col] = X[col].apply(
                        lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else -1
                    )
        
        # Scale numeric features
        scaling_info = preprocessor_info.get('scaling_info', {})
        if scaling_info.get('scaled', False):
            numeric_features = scaling_info['features']
            if self.scaler is not None:
                X[numeric_features] = self.scaler.transform(X[numeric_features])
        
        # Ensure column order matches training
        expected_features = preprocessor_info['feature_names']
        X = X.reindex(columns=expected_features, fill_value=0)
        
        return X.values
