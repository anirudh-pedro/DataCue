"""
Feature Engineer
Automated feature engineering to create new features from existing ones.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Automated feature engineering:
    - Datetime features extraction
    - Polynomial features
    - Interaction terms
    - Binning
    - Aggregations
    """
    
    def __init__(self):
        """Initialize feature engineer"""
        self.engineered_features = []
    
    def engineer_features(
        self,
        data: pd.DataFrame,
        problem_type: str,
        create_polynomials: bool = False,
        create_interactions: bool = False,
        polynomial_degree: int = 2
    ) -> pd.DataFrame:
        """
        Apply automated feature engineering.
        
        Args:
            data: Input DataFrame
            problem_type: 'classification' or 'regression'
            create_polynomials: Whether to create polynomial features
            create_interactions: Whether to create interaction terms
            polynomial_degree: Degree for polynomial features
            
        Returns:
            DataFrame with engineered features
        """
        df = data.copy()
        original_columns = set(df.columns)
        
        # 1. DateTime features
        df = self._extract_datetime_features(df)
        
        # 2. Numeric transformations
        df = self._create_numeric_transformations(df)
        
        # 3. Polynomial features (optional, can explode feature space)
        if create_polynomials:
            df = self._create_polynomial_features(df, polynomial_degree)
        
        # 4. Interaction features (optional)
        if create_interactions:
            df = self._create_interaction_features(df)
        
        # Track what was created
        new_columns = set(df.columns) - original_columns
        self.engineered_features = list(new_columns)
        
        if self.engineered_features:
            logger.info(f"   Created {len(self.engineered_features)} new features")
        
        return df
    
    def _extract_datetime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from datetime columns.
        
        Creates: year, month, day, day_of_week, quarter, is_weekend, etc.
        """
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        for col in datetime_cols:
            # Basic temporal features
            df[f'{col}_year'] = df[col].dt.year
            df[f'{col}_month'] = df[col].dt.month
            df[f'{col}_day'] = df[col].dt.day
            df[f'{col}_dayofweek'] = df[col].dt.dayofweek
            df[f'{col}_quarter'] = df[col].dt.quarter
            df[f'{col}_is_weekend'] = (df[col].dt.dayofweek >= 5).astype(int)
            df[f'{col}_hour'] = df[col].dt.hour if hasattr(df[col].dt, 'hour') else 0
            
            # Drop original datetime column (can't use directly in most models)
            df = df.drop(columns=[col])
        
        # Try to parse object columns as dates
        object_cols = df.select_dtypes(include=['object']).columns
        for col in object_cols:
            try:
                # Try to convert to datetime
                temp_date = pd.to_datetime(df[col], errors='coerce')
                # If more than 50% are valid dates, use it
                if temp_date.notna().sum() / len(df) > 0.5:
                    df[col] = temp_date
                    # Extract features
                    df[f'{col}_year'] = df[col].dt.year
                    df[f'{col}_month'] = df[col].dt.month
                    df[f'{col}_day'] = df[col].dt.day
                    df = df.drop(columns=[col])
            except:
                continue
        
        return df
    
    def _create_numeric_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create transformations of numeric features.
        
        Creates: log, sqrt, square for numeric columns
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Skip if already a transformed column
            if any(x in col for x in ['_log', '_sqrt', '_squared', '_year', '_month']):
                continue
            
            # Log transform (for positive skewed data)
            if (df[col] > 0).all():
                df[f'{col}_log'] = np.log1p(df[col])
            
            # Square root (for count data)
            if (df[col] >= 0).all():
                df[f'{col}_sqrt'] = np.sqrt(df[col])
            
            # Squared (for potential quadratic relationships)
            df[f'{col}_squared'] = df[col] ** 2
        
        return df
    
    def _create_polynomial_features(
        self,
        df: pd.DataFrame,
        degree: int = 2,
        max_features: int = 50
    ) -> pd.DataFrame:
        """
        Create polynomial features using sklearn.
        
        Warning: Can create many features quickly!
        """
        try:
            from sklearn.preprocessing import PolynomialFeatures
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Limit to prevent explosion
            if len(numeric_cols) > 10:
                logger.warning("Too many numeric columns for polynomial features, skipping")
                return df
            
            poly = PolynomialFeatures(degree=degree, include_bias=False)
            poly_features = poly.fit_transform(df[numeric_cols])
            
            # Limit number of new features
            if poly_features.shape[1] > max_features:
                logger.warning(f"Polynomial features would create {poly_features.shape[1]} features, limiting to {max_features}")
                poly_features = poly_features[:, :max_features]
            
            # Create feature names
            poly_names = [f'poly_{i}' for i in range(poly_features.shape[1])]
            
            # Add to DataFrame
            poly_df = pd.DataFrame(poly_features, columns=poly_names, index=df.index)
            df = pd.concat([df, poly_df], axis=1)
            
            # Remove original numeric columns to avoid duplication
            df = df.drop(columns=numeric_cols)
            
        except Exception as e:
            logger.warning(f"Polynomial feature creation failed: {str(e)}")
        
        return df
    
    def _create_interaction_features(
        self,
        df: pd.DataFrame,
        max_interactions: int = 20
    ) -> pd.DataFrame:
        """
        Create interaction terms between numeric features.
        
        Creates: feature_A * feature_B for top correlating pairs
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Limit to prevent explosion
        if len(numeric_cols) > 10:
            numeric_cols = numeric_cols[:10]
        
        interactions_created = 0
        
        # Create pairwise interactions
        for i, col1 in enumerate(numeric_cols):
            if interactions_created >= max_interactions:
                break
            
            for col2 in numeric_cols[i+1:]:
                if interactions_created >= max_interactions:
                    break
                
                # Multiplication interaction
                df[f'{col1}_x_{col2}'] = df[col1] * df[col2]
                
                # Division interaction (if no zeros)
                if (df[col2] != 0).all():
                    df[f'{col1}_div_{col2}'] = df[col1] / df[col2]
                
                interactions_created += 2
        
        return df
    
    def get_engineered_features(self) -> List[str]:
        """Return list of engineered feature names"""
        return self.engineered_features
