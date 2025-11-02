"""
Dashboard Designer Agent - Data Analyzer
Analyzes dataset structure to determine compatible chart options
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from models.dashboard_models import ChartType, DatasetInfo


class DataAnalyzer:
    """Analyzes dataset to provide smart chart recommendations"""
    
    def __init__(self):
        self.numeric_types = ['int64', 'float64', 'int32', 'float32']
        self.categorical_types = ['object', 'category', 'bool']
        self.datetime_types = ['datetime64[ns]', 'datetime64']
    
    def analyze_dataset(self, df: pd.DataFrame, dataset_id: str) -> DatasetInfo:
        """
        Analyze dataset and extract metadata
        
        Args:
            df: DataFrame to analyze
            dataset_id: Unique identifier for the dataset
            
        Returns:
            DatasetInfo with column types and metadata
        """
        column_types = {}
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            
            # Determine column type
            if dtype in self.numeric_types:
                column_types[col] = "numeric"
            elif dtype in self.datetime_types or pd.api.types.is_datetime64_any_dtype(df[col]):
                column_types[col] = "datetime"
            else:
                # Check if it's a numeric column stored as object
                try:
                    pd.to_numeric(df[col])
                    column_types[col] = "numeric"
                except:
                    # Check if it could be a date
                    try:
                        pd.to_datetime(df[col])
                        column_types[col] = "datetime"
                    except:
                        column_types[col] = "categorical"
        
        # Get sample data (first 5 rows)
        sample_data = {}
        for col in df.columns:
            sample_data[col] = df[col].head(5).tolist()
        
        return DatasetInfo(
            dataset_id=dataset_id,
            columns=df.columns.tolist(),
            column_types=column_types,
            row_count=len(df),
            sample_data=sample_data
        )
    
    def get_compatible_chart_types(
        self, 
        x_col_type: str, 
        y_col_type: str = None
    ) -> List[ChartType]:
        """
        Determine which chart types are compatible with given column types
        
        Args:
            x_col_type: Type of x-axis column (numeric, categorical, datetime)
            y_col_type: Type of y-axis column (optional)
            
        Returns:
            List of compatible ChartType enums
        """
        compatible_charts = []
        
        # Single column charts
        if not y_col_type:
            if x_col_type == "numeric":
                compatible_charts = [ChartType.HISTOGRAM, ChartType.BOX]
            elif x_col_type == "categorical":
                compatible_charts = [ChartType.BAR, ChartType.PIE]
        
        # Two column charts
        else:
            # Categorical x, Numeric y
            if x_col_type == "categorical" and y_col_type == "numeric":
                compatible_charts = [
                    ChartType.BAR, 
                    ChartType.PIE, 
                    ChartType.TREEMAP,
                    ChartType.FUNNEL
                ]
            
            # Datetime x, Numeric y
            elif x_col_type == "datetime" and y_col_type == "numeric":
                compatible_charts = [
                    ChartType.LINE, 
                    ChartType.AREA, 
                    ChartType.BAR,
                    ChartType.SCATTER
                ]
            
            # Numeric x, Numeric y
            elif x_col_type == "numeric" and y_col_type == "numeric":
                compatible_charts = [
                    ChartType.SCATTER, 
                    ChartType.LINE,
                    ChartType.HEATMAP
                ]
            
            # Categorical x, Categorical y
            elif x_col_type == "categorical" and y_col_type == "categorical":
                compatible_charts = [ChartType.HEATMAP]
        
        return compatible_charts
    
    def get_axis_options(
        self, 
        dataset_info: DatasetInfo, 
        chart_type: ChartType
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Get available x-axis, y-axis, and color options for a chart type
        
        Args:
            dataset_info: Dataset metadata
            chart_type: Selected chart type
            
        Returns:
            Tuple of (x_options, y_options, color_options)
        """
        x_options = []
        y_options = []
        color_options = []
        
        # Get columns by type
        numeric_cols = [col for col, ctype in dataset_info.column_types.items() if ctype == "numeric"]
        categorical_cols = [col for col, ctype in dataset_info.column_types.items() if ctype == "categorical"]
        datetime_cols = [col for col, ctype in dataset_info.column_types.items() if ctype == "datetime"]
        
        # Define options based on chart type
        if chart_type in [ChartType.BAR, ChartType.PIE, ChartType.TREEMAP, ChartType.FUNNEL]:
            x_options = categorical_cols
            y_options = numeric_cols
            color_options = categorical_cols
        
        elif chart_type in [ChartType.LINE, ChartType.AREA]:
            x_options = datetime_cols + numeric_cols
            y_options = numeric_cols
            color_options = categorical_cols
        
        elif chart_type == ChartType.SCATTER:
            x_options = numeric_cols
            y_options = numeric_cols
            color_options = categorical_cols + numeric_cols
        
        elif chart_type == ChartType.HISTOGRAM:
            x_options = numeric_cols
            y_options = []  # Histogram calculates frequency
            color_options = categorical_cols
        
        elif chart_type == ChartType.BOX:
            x_options = categorical_cols  # Grouping variable
            y_options = numeric_cols
            color_options = categorical_cols
        
        elif chart_type == ChartType.HEATMAP:
            x_options = categorical_cols + numeric_cols
            y_options = categorical_cols + numeric_cols
            color_options = []  # Heatmap uses value for color
        
        return x_options, y_options, color_options
    
    def recommend_default_axes(
        self, 
        dataset_info: DatasetInfo, 
        chart_type: ChartType,
        section_title: str = None
    ) -> Dict[str, str]:
        """
        Recommend default x and y axes based on chart type and data
        
        Args:
            dataset_info: Dataset metadata
            chart_type: Selected chart type
            section_title: Optional section title for context
            
        Returns:
            Dictionary with 'x_axis' and 'y_axis' recommendations
        """
        x_options, y_options, _ = self.get_axis_options(dataset_info, chart_type)
        
        recommendations = {}
        
        # Smart defaults based on column names and types
        if x_options:
            # Prefer date columns for time series
            if chart_type in [ChartType.LINE, ChartType.AREA]:
                datetime_cols = [col for col in x_options if dataset_info.column_types.get(col) == "datetime"]
                if datetime_cols:
                    recommendations['x_axis'] = datetime_cols[0]
                else:
                    recommendations['x_axis'] = x_options[0]
            else:
                recommendations['x_axis'] = x_options[0]
        
        if y_options:
            # Look for revenue, sales, amount, etc. in column names
            priority_keywords = ['revenue', 'sales', 'amount', 'total', 'value', 'price', 'cost']
            
            for keyword in priority_keywords:
                matching_cols = [col for col in y_options if keyword in col.lower()]
                if matching_cols:
                    recommendations['y_axis'] = matching_cols[0]
                    break
            
            # If no match, use first numeric column
            if 'y_axis' not in recommendations:
                recommendations['y_axis'] = y_options[0]
        
        return recommendations
    
    def get_aggregation_functions(self, chart_type: ChartType) -> List[str]:
        """
        Get available aggregation functions for a chart type
        
        Args:
            chart_type: Selected chart type
            
        Returns:
            List of aggregation function names
        """
        # Most charts support all aggregations
        base_aggregations = ["sum", "count", "avg", "min", "max"]
        
        # Some charts have specific aggregations
        if chart_type == ChartType.HISTOGRAM:
            return ["count"]  # Histogram only counts frequency
        
        elif chart_type in [ChartType.PIE, ChartType.FUNNEL]:
            return ["sum", "count"]  # Simpler aggregations for these
        
        return base_aggregations
    
    def validate_chart_config(
        self, 
        dataset_info: DatasetInfo,
        chart_type: ChartType,
        x_axis: str = None,
        y_axis: str = None,
        color_by: str = None
    ) -> Tuple[bool, str]:
        """
        Validate if a chart configuration is valid
        
        Args:
            dataset_info: Dataset metadata
            chart_type: Selected chart type
            x_axis: X-axis column name
            y_axis: Y-axis column name
            color_by: Color-by column name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        x_options, y_options, color_options = self.get_axis_options(dataset_info, chart_type)
        
        # Check x-axis
        if x_axis and x_axis not in dataset_info.columns:
            return False, f"Column '{x_axis}' not found in dataset"
        
        if x_axis and x_options and x_axis not in x_options:
            return False, f"Column '{x_axis}' is not compatible with {chart_type.value} chart as x-axis"
        
        # Check y-axis
        if y_axis and y_axis not in dataset_info.columns:
            return False, f"Column '{y_axis}' not found in dataset"
        
        if y_axis and y_options and y_axis not in y_options:
            return False, f"Column '{y_axis}' is not compatible with {chart_type.value} chart as y-axis"
        
        # Check color-by
        if color_by and color_by not in dataset_info.columns:
            return False, f"Column '{color_by}' not found in dataset"
        
        if color_by and color_options and color_by not in color_options:
            return False, f"Column '{color_by}' is not suitable for coloring in {chart_type.value} chart"
        
        # Chart-specific validations
        if chart_type in [ChartType.BAR, ChartType.PIE, ChartType.TREEMAP]:
            if not x_axis or not y_axis:
                return False, f"{chart_type.value} chart requires both x-axis and y-axis"
        
        elif chart_type in [ChartType.LINE, ChartType.AREA, ChartType.SCATTER]:
            if not x_axis or not y_axis:
                return False, f"{chart_type.value} chart requires both x-axis and y-axis"
        
        elif chart_type == ChartType.HISTOGRAM:
            if not x_axis:
                return False, "Histogram requires x-axis (numeric column)"
        
        return True, ""
