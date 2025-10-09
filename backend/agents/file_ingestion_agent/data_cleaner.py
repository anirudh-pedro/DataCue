"""
Data Cleaner Module
Handles data cleaning and standardization operations
"""

import pandas as pd
import numpy as np
import re
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Responsible for cleaning and standardizing uploaded datasets
    """
    
    def __init__(self):
        self.cleaning_stats = {}
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply complete cleaning pipeline to the DataFrame
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df_cleaned = df.copy()
        
        # Track cleaning statistics
        self.cleaning_stats = {
            "original_rows": len(df_cleaned),
            "original_columns": len(df_cleaned.columns),
            "missing_values_handled": 0,
            "duplicates_removed": 0,
            "columns_renamed": 0
        }
        
        # Step 1: Standardize column names
        df_cleaned = self._standardize_column_names(df_cleaned)
        
        # Step 2: Handle missing values
        df_cleaned = self._handle_missing_values(df_cleaned)
        
        # Step 3: Remove duplicate rows
        df_cleaned = self._remove_duplicates(df_cleaned)
        
        # Step 4: Clean data types
        df_cleaned = self._clean_data_types(df_cleaned)
        
        # Step 5: Remove completely empty rows/columns
        df_cleaned = self._remove_empty_rows_columns(df_cleaned)
        
        logger.info(f"Cleaning complete. Stats: {self.cleaning_stats}")
        
        return df_cleaned
    
    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names: lowercase, replace spaces with underscores, remove special chars
        """
        original_columns = df.columns.tolist()
        
        new_columns = []
        for col in df.columns:
            # Convert to string and lowercase
            col_name = str(col).lower()
            
            # Replace spaces and special characters with underscores
            col_name = re.sub(r'[^\w\s]', '', col_name)
            col_name = re.sub(r'\s+', '_', col_name)
            
            # Remove leading/trailing underscores
            col_name = col_name.strip('_')
            
            # Handle empty column names
            if not col_name:
                col_name = f"column_{len(new_columns)}"
            
            new_columns.append(col_name)
        
        # Handle duplicate column names
        seen = {}
        unique_columns = []
        for col in new_columns:
            if col in seen:
                seen[col] += 1
                unique_columns.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                unique_columns.append(col)
        
        df.columns = unique_columns
        
        renamed_count = sum(1 for old, new in zip(original_columns, unique_columns) if old != new)
        self.cleaning_stats["columns_renamed"] = renamed_count
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values based on column type
        """
        missing_before = df.isnull().sum().sum()
        
        for col in df.columns:
            if df[col].isnull().any():
                # Numeric columns: fill with median
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col].fillna(df[col].median(), inplace=True)
                
                # Categorical/Object columns: fill with mode or 'Unknown'
                elif pd.api.types.is_object_dtype(df[col]):
                    mode_value = df[col].mode()
                    if len(mode_value) > 0:
                        df[col].fillna(mode_value[0], inplace=True)
                    else:
                        df[col].fillna('Unknown', inplace=True)
                
                # DateTime columns: forward fill
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col].fillna(method='ffill', inplace=True)
        
        missing_after = df.isnull().sum().sum()
        self.cleaning_stats["missing_values_handled"] = missing_before - missing_after
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate rows
        """
        rows_before = len(df)
        df = df.drop_duplicates()
        rows_after = len(df)
        
        self.cleaning_stats["duplicates_removed"] = rows_before - rows_after
        
        return df
    
    def _clean_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Attempt to convert columns to appropriate data types
        """
        for col in df.columns:
            # Skip if already numeric or datetime
            if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(df[col]):
                continue
            
            # Try to convert to numeric
            try:
                converted_numeric = pd.to_numeric(df[col], errors='coerce')
                if converted_numeric.notna().any():
                    df[col] = df[col].where(converted_numeric.isna(), converted_numeric)
            except Exception:
                pass
            
            # Try to convert to datetime if it looks like a date
            if pd.api.types.is_object_dtype(df[col]):
                try:
                    # Sample first non-null value
                    sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
                    if sample and any(char in str(sample) for char in ['-', '/', ':']):
                        converted_datetime = pd.to_datetime(df[col], errors='coerce', utc=False)
                        if converted_datetime.notna().any():
                            df[col] = df[col].where(converted_datetime.isna(), converted_datetime)
                except Exception:
                    pass
        
        return df
    
    def _remove_empty_rows_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove completely empty rows and columns
        """
        # Remove columns that are completely null
        df = df.dropna(axis=1, how='all')
        
        # Remove rows that are completely null
        df = df.dropna(axis=0, how='all')
        
        return df
    
    def get_cleaning_stats(self) -> dict:
        """
        Return the statistics from the last cleaning operation
        """
        return self.cleaning_stats
