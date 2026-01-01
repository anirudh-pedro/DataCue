"""
Result Type Detector Module
Detects the appropriate visualization type for query results
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class ResultTypeDetector:
    """
    Detects the best visualization type for query results
    
    Result Types:
    - kpi: Single number (count, sum, average)
    - table: Multiple rows/columns of data
    - line_chart: Time-series data
    - bar_chart: Categorical comparison
    - pie_chart: Proportions/percentages
    """
    
    def detect(
        self, 
        result: Union[pd.DataFrame, pd.Series, int, float, str, np.ndarray, list],
        query: str = "",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Detect the best result type and format data accordingly
        
        Args:
            result: Query execution result
            query: Original query string (for context)
            metadata: Column metadata from dataset
            
        Returns:
            {
                "type": "kpi" | "table" | "list" | "line_chart" | "bar_chart" | "pie_chart" | "text",
                "data": formatted data for frontend,
                "config": visualization config,
                "meta": additional metadata
            }
        """
        # Normalize result to JSON-serializable format first
        result = self._normalize_result(result)
        
        # Handle None/NaN
        if result is None or (isinstance(result, float) and pd.isna(result)):
            return {
                "type": "text",
                "data": {"value": "No result"},
                "config": {},
                "meta": {"empty": True}
            }
        
        # Handle scalar values (single number)
        if isinstance(result, (int, float, np.integer, np.floating)):
            return self._format_kpi(float(result), query)
        
        # Handle boolean
        if isinstance(result, (bool, np.bool_)):
            return self._format_text(str(result))
        
        # Handle string results
        if isinstance(result, str):
            return self._format_text(result)
        
        # Handle numpy arrays
        if isinstance(result, np.ndarray):
            return self._format_numpy_array(result, query)
        
        # Handle plain Python lists
        if isinstance(result, list):
            return self._format_list(result, query)
        
        # Convert Series to DataFrame for consistent handling
        if isinstance(result, pd.Series):
            return self._format_series(result, query)
        
        # Handle DataFrame
        if isinstance(result, pd.DataFrame):
            return self._detect_dataframe_type(result, query, metadata)
        
        # Fallback for unknown types - convert to string but warn
        return {
            "type": "text",
            "data": {"value": str(result)},
            "config": {},
            "meta": {"warning": f"Unknown result type: {type(result).__name__}"}
        }
    
    def _normalize_result(self, result: Any) -> Any:
        """
        Normalize pandas/numpy objects to standard Python types for JSON serialization.
        This ensures all downstream processing works with clean, serializable data.
        """
        # Handle None
        if result is None:
            return None
        
        # Handle numpy scalar types
        if isinstance(result, (np.integer, np.floating)):
            return result.item()
        
        if isinstance(result, np.bool_):
            return bool(result)
        
        if isinstance(result, np.ndarray):
            # Keep as ndarray for further processing
            return result
        
        # Handle pandas nullable types
        if pd.api.types.is_scalar(result) and pd.isna(result):
            return None
        
        # Return as-is for complex types (Series, DataFrame, list, etc.)
        return result
    
    def _format_numpy_array(self, arr: np.ndarray, query: str = "") -> Dict[str, Any]:
        """
        Format numpy array result.
        Arrays can be:
        - 1D with unique values (e.g., df['col'].unique())
        - 1D with aggregated values
        - Multi-dimensional (convert to table)
        """
        # Handle empty array
        if arr.size == 0:
            return {
                "type": "list",
                "data": {"items": []},
                "config": {},
                "meta": {"empty": True, "original_type": "numpy.ndarray"}
            }
        
        # Flatten if multi-dimensional
        if arr.ndim > 1:
            # Convert to list of lists for table-like display
            items = arr.tolist()
            return {
                "type": "table",
                "data": {
                    "columns": [f"col_{i}" for i in range(arr.shape[1])],
                    "rows": [dict(zip([f"col_{i}" for i in range(arr.shape[1])], row)) for row in items],
                    "total_rows": len(items)
                },
                "config": {},
                "meta": {"shape": arr.shape, "original_type": "numpy.ndarray"}
            }
        
        # 1D array - convert to Python list
        items = arr.tolist()
        
        # Single item - check if it should be KPI
        if len(items) == 1:
            if isinstance(items[0], (int, float)):
                return self._format_kpi(items[0], query)
        
        # Multiple items - return as list
        return {
            "type": "list",
            "data": {
                "items": items,
                "count": len(items)
            },
            "config": {},
            "meta": {"original_type": "numpy.ndarray", "dtype": str(arr.dtype)}
        }
    
    def _format_list(self, items: list, query: str = "") -> Dict[str, Any]:
        """
        Format plain Python list result.
        """
        # Handle empty list
        if not items:
            return {
                "type": "list",
                "data": {"items": []},
                "config": {},
                "meta": {"empty": True}
            }
        
        # Single item list - might be KPI
        if len(items) == 1:
            if isinstance(items[0], (int, float)):
                return self._format_kpi(items[0], query)
            if isinstance(items[0], dict):
                # Single dict - format as table with one row
                return {
                    "type": "table",
                    "data": {
                        "columns": list(items[0].keys()),
                        "rows": items,
                        "total_rows": 1
                    },
                    "config": {},
                    "meta": {}
                }
        
        # Check if list of dicts (table-like)
        if all(isinstance(item, dict) for item in items):
            # Extract columns from first dict
            if items:
                columns = list(items[0].keys())
                return {
                    "type": "table",
                    "data": {
                        "columns": columns,
                        "rows": items[:100],  # Limit to 100 rows
                        "total_rows": len(items)
                    },
                    "config": {"truncated": len(items) > 100},
                    "meta": {}
                }
        
        # Plain list of values
        return {
            "type": "list",
            "data": {
                "items": items[:100],  # Limit to 100 items
                "count": len(items)
            },
            "config": {"truncated": len(items) > 100},
            "meta": {}
        }
    
    def _format_series(self, series: pd.Series, query: str = "") -> Dict[str, Any]:
        """
        Format pandas Series result.
        Series can be:
        - Single value (KPI)
        - Multiple values with index (table)
        - Named series (use name as column)
        """
        # Handle empty series
        if series.empty:
            return {
                "type": "list",
                "data": {"items": []},
                "config": {},
                "meta": {"empty": True, "original_type": "pandas.Series"}
            }
        
        # Single value - return as KPI if numeric
        if len(series) == 1:
            value = series.iloc[0]
            if isinstance(value, (int, float, np.number)):
                return self._format_kpi(float(value), query)
        
        # Convert to DataFrame for consistent handling
        df = series.reset_index()
        
        # Rename columns for clarity
        if len(df.columns) == 2:
            # Series with index becomes two columns
            df.columns = ['index', series.name or 'value']
        
        return self._detect_dataframe_type(df, query, None)
    
    def _format_kpi(self, value: Union[int, float], query: str = "") -> Dict[str, Any]:
        """Format single number as KPI"""
        # Detect if it's a percentage, currency, or plain number
        query_lower = query.lower()
        
        format_type = "number"
        if 'percent' in query_lower or 'rate' in query_lower or 'ratio' in query_lower:
            format_type = "percentage"
        elif 'price' in query_lower or 'revenue' in query_lower or 'cost' in query_lower or 'amount' in query_lower or 'salary' in query_lower:
            format_type = "currency"
        elif 'count' in query_lower:
            format_type = "integer"
        
        return {
            "type": "kpi",
            "data": {
                "value": float(value) if not pd.isna(value) else 0,
                "formatted": self._format_number(value, format_type)
            },
            "config": {
                "format": format_type
            },
            "meta": {}
        }
    
    def _format_text(self, text: str) -> Dict[str, Any]:
        """Format text result"""
        return {
            "type": "text",
            "data": {"value": text},
            "config": {},
            "meta": {}
        }
    
    def _detect_dataframe_type(
        self, 
        df: pd.DataFrame, 
        query: str = "",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Detect the best visualization for a DataFrame result"""
        
        if df.empty:
            return {
                "type": "table",
                "data": {
                    "columns": [],
                    "rows": [],
                    "total_rows": 0
                },
                "config": {"empty": True},
                "meta": {}
            }
        
        # Single cell result → KPI
        if len(df) == 1 and len(df.columns) == 1:
            value = df.iloc[0, 0]
            if isinstance(value, (int, float)):
                return self._format_kpi(value, query)
        
        # Detect column types
        has_datetime = False
        has_numeric = False
        has_categorical = False
        datetime_col = None
        numeric_cols = []
        categorical_cols = []
        
        for col in df.columns:
            dtype = df[col].dtype
            
            if pd.api.types.is_datetime64_any_dtype(dtype):
                has_datetime = True
                datetime_col = col
            elif self._is_datetime_column(df[col]):
                has_datetime = True
                datetime_col = col
            elif pd.api.types.is_numeric_dtype(dtype):
                has_numeric = True
                numeric_cols.append(col)
            else:
                has_categorical = True
                categorical_cols.append(col)
        
        # Time-series detection (datetime + numeric)
        if has_datetime and has_numeric and len(df) > 2:
            return self._format_line_chart(df, datetime_col, numeric_cols[0])
        
        # Grouped aggregation (categorical + single numeric)
        if has_categorical and has_numeric:
            cat_col = categorical_cols[0] if categorical_cols else df.columns[0]
            num_col = numeric_cols[0] if numeric_cols else df.columns[-1]
            
            # Pie chart for proportions (few categories)
            if len(df) <= 8 and 'percent' in query.lower():
                return self._format_pie_chart(df, cat_col, num_col)
            
            # Bar chart for comparisons
            if len(df) <= 20:
                return self._format_bar_chart(df, cat_col, num_col)
        
        # Default to table
        return self._format_table(df)
    
    def _is_datetime_column(self, series: pd.Series) -> bool:
        """Check if a column looks like datetime"""
        if series.dtype == 'object':
            try:
                sample = series.dropna().head(5)
                if len(sample) == 0:
                    return False
                # Try to parse as datetime
                pd.to_datetime(sample)
                return True
            except:
                return False
        return False
    
    def _format_line_chart(
        self, 
        df: pd.DataFrame, 
        x_col: str, 
        y_col: str
    ) -> Dict[str, Any]:
        """Format data for line chart"""
        # Sort by x-axis (datetime)
        df_sorted = df.sort_values(by=x_col)
        
        return {
            "type": "line_chart",
            "data": {
                "x": df_sorted[x_col].astype(str).tolist(),
                "y": df_sorted[y_col].tolist(),
                "x_label": x_col,
                "y_label": y_col
            },
            "config": {
                "chart_type": "line",
                "x_axis": x_col,
                "y_axis": y_col,
                "title": f"{y_col} over {x_col}"
            },
            "meta": {}
        }
    
    def _format_bar_chart(
        self, 
        df: pd.DataFrame, 
        x_col: str, 
        y_col: str
    ) -> Dict[str, Any]:
        """Format data for bar chart"""
        # Sort by value descending
        df_sorted = df.sort_values(by=y_col, ascending=False)
        
        return {
            "type": "bar_chart",
            "data": {
                "labels": df_sorted[x_col].astype(str).tolist(),
                "values": df_sorted[y_col].tolist(),
                "x_label": x_col,
                "y_label": y_col
            },
            "config": {
                "chart_type": "bar",
                "x_axis": x_col,
                "y_axis": y_col,
                "title": f"{y_col} by {x_col}"
            },
            "meta": {}
        }
    
    def _format_pie_chart(
        self, 
        df: pd.DataFrame, 
        label_col: str, 
        value_col: str
    ) -> Dict[str, Any]:
        """Format data for pie chart"""
        return {
            "type": "pie_chart",
            "data": {
                "labels": df[label_col].astype(str).tolist(),
                "values": df[value_col].tolist()
            },
            "config": {
                "chart_type": "pie",
                "title": f"{value_col} by {label_col}"
            },
            "meta": {}
        }
    
    def _format_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Format data as table"""
        # Convert DataFrame to JSON-serializable format
        # Handle datetime columns
        df_copy = df.copy()
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].astype(str)
        
        # Limit to 100 rows
        df_limited = df_copy.head(100)
        
        # Convert to records, handling NaN/None values
        rows = df_limited.to_dict(orient='records')
        
        # Clean up NaN values for JSON serialization
        for row in rows:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None
                elif isinstance(value, (np.integer, np.floating)):
                    row[key] = value.item()
        
        return {
            "type": "table",
            "data": {
                "columns": df_limited.columns.tolist(),
                "rows": rows,
                "total_rows": len(df)
            },
            "config": {
                "truncated": len(df) > 100,
                "original_row_count": len(df)
            },
            "meta": {}
        }
    
    def _format_number(self, value: Union[int, float], format_type: str) -> str:
        """Format number for display"""
        if pd.isna(value):
            return "N/A"
        
        if format_type == "percentage":
            return f"{value:.2f}%"
        elif format_type == "currency":
            if abs(value) >= 1_000_000:
                return f"${value/1_000_000:.2f}M"
            elif abs(value) >= 1_000:
                return f"${value/1_000:.2f}K"
            else:
                return f"${value:.2f}"
        elif format_type == "integer":
            return f"{int(value):,}"
        else:
            if abs(value) >= 1_000_000:
                return f"{value/1_000_000:.2f}M"
            elif abs(value) >= 1_000:
                return f"{value/1_000:.2f}K"
            else:
                return f"{value:.2f}" if isinstance(value, float) else str(value)


def detect_result_type(
    result: Union[pd.DataFrame, pd.Series, int, float, str],
    query: str = "",
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Convenience function for result type detection"""
    detector = ResultTypeDetector()
    return detector.detect(result, query, metadata)
