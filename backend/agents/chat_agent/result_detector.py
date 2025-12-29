"""
Result Type Detector Module
Detects the appropriate visualization type for query results
"""

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
        result: Union[pd.DataFrame, pd.Series, int, float, str],
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
                "type": "kpi" | "table" | "line_chart" | "bar_chart" | "pie_chart",
                "data": formatted data for frontend,
                "config": visualization config
            }
        """
        # Handle scalar values (single number)
        if isinstance(result, (int, float)):
            return self._format_kpi(result, query)
        
        # Handle string results
        if isinstance(result, str):
            return self._format_text(result)
        
        # Convert Series to DataFrame for consistent handling
        if isinstance(result, pd.Series):
            result = result.reset_index()
            if len(result.columns) == 2:
                result.columns = ['category', 'value']
        
        # Handle DataFrame
        if isinstance(result, pd.DataFrame):
            return self._detect_dataframe_type(result, query, metadata)
        
        # Fallback for unknown types
        return {
            "type": "text",
            "data": {"value": str(result)},
            "config": {}
        }
    
    def _format_kpi(self, value: Union[int, float], query: str = "") -> Dict[str, Any]:
        """Format single number as KPI"""
        # Detect if it's a percentage, currency, or plain number
        query_lower = query.lower()
        
        format_type = "number"
        if 'percent' in query_lower or 'rate' in query_lower or 'ratio' in query_lower:
            format_type = "percentage"
        elif 'price' in query_lower or 'revenue' in query_lower or 'cost' in query_lower or 'amount' in query_lower:
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
            }
        }
    
    def _format_text(self, text: str) -> Dict[str, Any]:
        """Format text result"""
        return {
            "type": "text",
            "data": {"value": text},
            "config": {}
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
                "data": [],
                "config": {"empty": True}
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
            }
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
            }
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
            }
        }
    
    def _format_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Format data as table"""
        # Limit to 100 rows
        df_limited = df.head(100)
        
        return {
            "type": "table",
            "data": {
                "columns": df_limited.columns.tolist(),
                "rows": df_limited.to_dict(orient='records'),
                "total_rows": len(df)
            },
            "config": {
                "truncated": len(df) > 100,
                "original_row_count": len(df)
            }
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
