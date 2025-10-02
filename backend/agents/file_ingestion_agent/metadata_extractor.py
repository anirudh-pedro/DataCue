"""
Metadata Extractor Module
Extracts comprehensive metadata from cleaned datasets
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extracts metadata including column info, data types, and statistics
    """
    
    def extract_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from DataFrame
        
        Args:
            df: Cleaned DataFrame
            
        Returns:
            Dictionary with metadata including:
                - columns: List of column info
                - shape: Dataset dimensions
                - summary_stats: Overall statistics
                - data_types_summary: Type distribution
        """
        try:
            metadata = {
                "shape": {
                    "rows": len(df),
                    "columns": len(df.columns)
                },
                "columns": self._extract_column_metadata(df),
                "summary_stats": self._extract_summary_stats(df),
                "data_types_summary": self._get_data_type_summary(df),
                "memory_usage": self._get_memory_usage(df),
                "data_quality_score": self._calculate_data_quality_score(df),
                "correlation_matrix": self._get_correlation_matrix(df),
                "advanced_insights": self._get_advanced_insights(df)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            raise
    
    def _extract_column_metadata(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extract detailed metadata for each column
        """
        columns_metadata = []
        
        for col in df.columns:
            col_data = df[col]
            
            col_info = {
                "name": col,
                "data_type": str(col_data.dtype),
                "python_type": self._get_python_type(col_data),
                "non_null_count": int(col_data.count()),
                "null_count": int(col_data.isnull().sum()),
                "null_percentage": round(col_data.isnull().sum() / len(df) * 100, 2),
                "unique_count": int(col_data.nunique()),
                "unique_percentage": round(col_data.nunique() / len(df) * 100, 2) if len(df) > 0 else 0,
                # Advanced features
                "chart_recommendations": self._recommend_charts(col_data, col),
                "is_high_cardinality": self._is_high_cardinality(col_data),
                "is_time_series": self._is_time_series(col_data),
                "suggested_role": self._suggest_column_role(col_data, col)
            }
            
            # Add type-specific statistics
            if pd.api.types.is_numeric_dtype(col_data):
                col_info.update(self._get_numeric_stats(col_data))
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                col_info.update(self._get_datetime_stats(col_data))
            else:
                col_info.update(self._get_categorical_stats(col_data))
            
            columns_metadata.append(col_info)
        
        return columns_metadata
    
    def _get_python_type(self, series: pd.Series) -> str:
        """
        Get simplified Python type for the column
        """
        dtype = series.dtype
        
        if pd.api.types.is_integer_dtype(dtype):
            return "integer"
        elif pd.api.types.is_float_dtype(dtype):
            return "float"
        elif pd.api.types.is_bool_dtype(dtype):
            return "boolean"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return "datetime"
        elif pd.api.types.is_object_dtype(dtype):
            return "string"
        else:
            return "other"
    
    def _get_numeric_stats(self, series: pd.Series) -> Dict[str, Any]:
        """
        Extract statistics for numeric columns
        """
        try:
            return {
                "stats_type": "numeric",
                "min": float(series.min()) if not pd.isna(series.min()) else None,
                "max": float(series.max()) if not pd.isna(series.max()) else None,
                "mean": float(series.mean()) if not pd.isna(series.mean()) else None,
                "median": float(series.median()) if not pd.isna(series.median()) else None,
                "std": float(series.std()) if not pd.isna(series.std()) else None,
                "q25": float(series.quantile(0.25)) if not pd.isna(series.quantile(0.25)) else None,
                "q75": float(series.quantile(0.75)) if not pd.isna(series.quantile(0.75)) else None,
                "skewness": float(series.skew()) if not pd.isna(series.skew()) else None,
                "kurtosis": float(series.kurtosis()) if not pd.isna(series.kurtosis()) else None,
                "zeros_count": int((series == 0).sum()),
                "negative_count": int((series < 0).sum()),
                "positive_count": int((series > 0).sum())
            }
        except Exception as e:
            logger.warning(f"Error getting numeric stats: {str(e)}")
            return {"stats_type": "numeric", "error": str(e)}
    
    def _get_datetime_stats(self, series: pd.Series) -> Dict[str, Any]:
        """
        Extract statistics for datetime columns
        """
        try:
            return {
                "stats_type": "datetime",
                "min_date": str(series.min()) if not pd.isna(series.min()) else None,
                "max_date": str(series.max()) if not pd.isna(series.max()) else None,
                "date_range_days": (series.max() - series.min()).days if not pd.isna(series.min()) else None
            }
        except Exception as e:
            logger.warning(f"Error getting datetime stats: {str(e)}")
            return {"stats_type": "datetime", "error": str(e)}
    
    def _get_categorical_stats(self, series: pd.Series) -> Dict[str, Any]:
        """
        Extract statistics for categorical/string columns
        """
        try:
            value_counts = series.value_counts()
            top_values = value_counts.head(10).to_dict()
            
            return {
                "stats_type": "categorical",
                "most_frequent": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                "most_frequent_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else None,
                "least_frequent": str(value_counts.index[-1]) if len(value_counts) > 0 else None,
                "least_frequent_count": int(value_counts.iloc[-1]) if len(value_counts) > 0 else None,
                "top_10_values": {str(k): int(v) for k, v in top_values.items()},
                "avg_length": float(series.astype(str).str.len().mean()) if len(series) > 0 else None,
                "min_length": int(series.astype(str).str.len().min()) if len(series) > 0 else None,
                "max_length": int(series.astype(str).str.len().max()) if len(series) > 0 else None
            }
        except Exception as e:
            logger.warning(f"Error getting categorical stats: {str(e)}")
            return {"stats_type": "categorical", "error": str(e)}
    
    def _extract_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract overall dataset summary statistics
        """
        return {
            "total_cells": len(df) * len(df.columns),
            "total_missing_cells": int(df.isnull().sum().sum()),
            "missing_percentage": round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2) if len(df) > 0 else 0,
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_columns": int(df.select_dtypes(include=[np.number]).shape[1]),
            "categorical_columns": int(df.select_dtypes(include=['object']).shape[1]),
            "datetime_columns": int(df.select_dtypes(include=['datetime64']).shape[1])
        }
    
    def _get_data_type_summary(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Get count of columns by data type
        """
        type_counts = df.dtypes.value_counts().to_dict()
        return {str(k): int(v) for k, v in type_counts.items()}
    
    def _get_memory_usage(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Get memory usage information
        """
        memory_bytes = df.memory_usage(deep=True).sum()
        
        # Convert to human-readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if memory_bytes < 1024.0:
                return {
                    "total": f"{memory_bytes:.2f} {unit}",
                    "bytes": int(memory_bytes)
                }
            memory_bytes /= 1024.0
        
        return {
            "total": f"{memory_bytes:.2f} TB",
            "bytes": int(memory_bytes * 1024**4)
        }
    
    # ==================== ADVANCED FEATURES ====================
    
    def _recommend_charts(self, series: pd.Series, col_name: str) -> List[str]:
        """
        Recommend appropriate chart types based on column characteristics
        """
        recommendations = []
        
        # Numeric columns
        if pd.api.types.is_numeric_dtype(series):
            recommendations.append("histogram")
            recommendations.append("box_plot")
            recommendations.append("line_chart")
            
            # If few unique values, could be categorical
            if series.nunique() < 10:
                recommendations.append("bar_chart")
                recommendations.append("pie_chart")
        
        # Datetime columns
        elif pd.api.types.is_datetime64_any_dtype(series):
            recommendations.append("time_series")
            recommendations.append("line_chart")
            recommendations.append("area_chart")
        
        # Categorical columns
        else:
            unique_count = series.nunique()
            
            if unique_count <= 10:
                recommendations.extend(["bar_chart", "pie_chart", "donut_chart"])
            elif unique_count <= 50:
                recommendations.extend(["bar_chart", "horizontal_bar"])
            else:
                recommendations.extend(["word_cloud", "treemap"])
        
        return recommendations
    
    def _is_high_cardinality(self, series: pd.Series) -> Dict[str, Any]:
        """
        Detect if column has high cardinality (too many unique values)
        """
        unique_count = series.nunique()
        total_count = len(series)
        unique_ratio = unique_count / total_count if total_count > 0 else 0
        
        # High cardinality thresholds
        is_high = False
        reason = None
        
        if pd.api.types.is_numeric_dtype(series):
            # Numeric columns naturally have many unique values
            is_high = False
        elif unique_ratio > 0.95:
            is_high = True
            reason = f"Nearly unique values ({unique_ratio:.1%})"
        elif unique_count > 100 and unique_ratio > 0.5:
            is_high = True
            reason = f"Many unique values ({unique_count} out of {total_count})"
        
        return {
            "is_high_cardinality": is_high,
            "unique_count": unique_count,
            "unique_ratio": round(unique_ratio, 3),
            "reason": reason,
            "recommendation": "Consider grouping or binning values" if is_high else None
        }
    
    def _is_time_series(self, series: pd.Series) -> Dict[str, Any]:
        """
        Detect if column represents time series data
        """
        is_ts = False
        confidence = "low"
        indicators = []
        
        # Direct datetime check
        if pd.api.types.is_datetime64_any_dtype(series):
            is_ts = True
            confidence = "high"
            indicators.append("datetime_dtype")
        
        # Check column name for time-related keywords
        col_name_lower = str(series.name).lower()
        time_keywords = ['date', 'time', 'timestamp', 'year', 'month', 'day', 'hour', 
                        'created', 'updated', 'modified', 'period', 'quarter']
        
        if any(keyword in col_name_lower for keyword in time_keywords):
            indicators.append("time_related_name")
            if not is_ts:
                is_ts = True
                confidence = "medium"
        
        # Check for sequential pattern (if numeric)
        if pd.api.types.is_numeric_dtype(series) and len(series) > 1:
            try:
                diff = series.diff().dropna()
                if len(diff) > 0:
                    # Check if differences are relatively constant (time series pattern)
                    diff_std = diff.std()
                    diff_mean = diff.mean()
                    if diff_mean != 0 and (diff_std / abs(diff_mean)) < 0.5:
                        indicators.append("sequential_pattern")
                        if not is_ts:
                            is_ts = True
                            confidence = "low"
            except:
                pass
        
        return {
            "is_time_series": is_ts,
            "confidence": confidence,
            "indicators": indicators,
            "recommendation": "Use for x-axis in time series plots" if is_ts else None
        }
    
    def _suggest_column_role(self, series: pd.Series, col_name: str) -> Dict[str, Any]:
        """
        Suggest the role/purpose of the column for AI and visualization
        """
        role = "unknown"
        suggestions = []
        
        col_name_lower = col_name.lower()
        unique_count = series.nunique()
        total_count = len(series)
        unique_ratio = unique_count / total_count if total_count > 0 else 0
        
        # Identifier column (ID, key, etc.)
        if unique_ratio > 0.95 or any(keyword in col_name_lower for keyword in ['id', 'key', 'uuid', 'code']):
            role = "identifier"
            suggestions.append("Not suitable for aggregation")
            suggestions.append("Can be used for filtering/grouping")
        
        # Measure/Metric (numeric values for aggregation)
        elif pd.api.types.is_numeric_dtype(series):
            if any(keyword in col_name_lower for keyword in ['amount', 'price', 'cost', 'revenue', 'sales', 
                                                               'quantity', 'count', 'total', 'value', 'score']):
                role = "measure"
                suggestions.append("Suitable for SUM, AVG, MIN, MAX aggregations")
                suggestions.append("Good for y-axis in charts")
            else:
                role = "numeric_attribute"
                suggestions.append("Can be used for calculations")
        
        # Dimension (categorical for grouping)
        elif unique_count < 50 and unique_count > 1:
            role = "dimension"
            suggestions.append("Suitable for GROUP BY operations")
            suggestions.append("Good for categorical charts")
            suggestions.append("Can be used as legend/color in visualizations")
        
        # Time dimension
        elif pd.api.types.is_datetime64_any_dtype(series):
            role = "time_dimension"
            suggestions.append("Use for time-based analysis")
            suggestions.append("Good for x-axis in time series")
            suggestions.append("Can be used for date filtering")
        
        # High cardinality text
        elif unique_count > 50:
            role = "text_attribute"
            suggestions.append("May need grouping or binning")
            suggestions.append("Consider word cloud for visualization")
        
        return {
            "role": role,
            "suggestions": suggestions,
            "is_suitable_for_aggregation": role in ["measure", "numeric_attribute"],
            "is_suitable_for_grouping": role in ["dimension", "time_dimension"]
        }
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate overall data quality score (0-100)
        """
        scores = {}
        weights = {}
        
        # 1. Completeness (30%)
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = (1 - missing_cells / total_cells) * 100 if total_cells > 0 else 0
        scores['completeness'] = round(completeness, 2)
        weights['completeness'] = 0.30
        
        # 2. Uniqueness (20%)
        duplicate_rows = df.duplicated().sum()
        uniqueness = (1 - duplicate_rows / len(df)) * 100 if len(df) > 0 else 0
        scores['uniqueness'] = round(uniqueness, 2)
        weights['uniqueness'] = 0.20
        
        # 3. Consistency (25%)
        # Check data type consistency (all values in column match expected type)
        consistent_cols = 0
        for col in df.columns:
            try:
                if pd.api.types.is_numeric_dtype(df[col]):
                    # Check if all non-null values are numeric
                    if df[col].dropna().apply(lambda x: isinstance(x, (int, float, np.number))).all():
                        consistent_cols += 1
                else:
                    consistent_cols += 1
            except:
                pass
        
        consistency = (consistent_cols / len(df.columns)) * 100 if len(df.columns) > 0 else 0
        scores['consistency'] = round(consistency, 2)
        weights['consistency'] = 0.25
        
        # 4. Validity (25%)
        # Check for outliers in numeric columns
        valid_cols = 0
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in df.columns:
            if col in numeric_cols:
                # Check for extreme outliers (beyond 3 std devs)
                if len(df[col].dropna()) > 0:
                    mean = df[col].mean()
                    std = df[col].std()
                    if std > 0:
                        outliers = ((df[col] - mean).abs() > 3 * std).sum()
                        if outliers / len(df) < 0.05:  # Less than 5% outliers
                            valid_cols += 1
                    else:
                        valid_cols += 1
            else:
                valid_cols += 1
        
        validity = (valid_cols / len(df.columns)) * 100 if len(df.columns) > 0 else 0
        scores['validity'] = round(validity, 2)
        weights['validity'] = 0.25
        
        # Calculate weighted overall score
        overall_score = sum(scores[key] * weights[key] for key in scores.keys())
        
        # Quality rating
        if overall_score >= 90:
            rating = "excellent"
        elif overall_score >= 75:
            rating = "good"
        elif overall_score >= 60:
            rating = "fair"
        else:
            rating = "poor"
        
        return {
            "overall_score": round(overall_score, 2),
            "rating": rating,
            "scores": scores,
            "issues": self._identify_quality_issues(df, scores)
        }
    
    def _identify_quality_issues(self, df: pd.DataFrame, scores: Dict[str, float]) -> List[str]:
        """
        Identify specific data quality issues
        """
        issues = []
        
        if scores['completeness'] < 90:
            missing_pct = 100 - scores['completeness']
            issues.append(f"Missing values: {missing_pct:.1f}% of cells are empty")
        
        if scores['uniqueness'] < 95:
            dup_count = df.duplicated().sum()
            issues.append(f"Duplicate rows: {dup_count} duplicate rows found")
        
        if scores['validity'] < 80:
            issues.append("Data validity: Potential outliers or invalid values detected")
        
        # Check for high cardinality columns
        for col in df.columns:
            unique_ratio = df[col].nunique() / len(df) if len(df) > 0 else 0
            if unique_ratio > 0.95 and not pd.api.types.is_numeric_dtype(df[col]):
                issues.append(f"High cardinality: Column '{col}' has too many unique values")
        
        return issues if issues else ["No major quality issues detected"]
    
    def _get_correlation_matrix(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate correlation matrix for numeric columns
        """
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            
            if len(numeric_df.columns) < 2:
                return {
                    "available": False,
                    "reason": "Not enough numeric columns (minimum 2 required)"
                }
            
            corr_matrix = numeric_df.corr()
            
            # Find strong correlations (|r| > 0.7)
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:
                        strong_correlations.append({
                            "column1": corr_matrix.columns[i],
                            "column2": corr_matrix.columns[j],
                            "correlation": round(float(corr_value), 3),
                            "strength": "strong positive" if corr_value > 0.7 else "strong negative"
                        })
            
            return {
                "available": True,
                "matrix": corr_matrix.to_dict(),
                "strong_correlations": strong_correlations,
                "columns_analyzed": list(numeric_df.columns)
            }
        
        except Exception as e:
            logger.warning(f"Error calculating correlation matrix: {str(e)}")
            return {
                "available": False,
                "reason": f"Error: {str(e)}"
            }
    
    def _get_advanced_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate advanced insights and recommendations
        """
        insights = {
            "suggested_visualizations": [],
            "data_characteristics": [],
            "recommendations": []
        }
        
        # Detect dataset type
        numeric_ratio = len(df.select_dtypes(include=[np.number]).columns) / len(df.columns)
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        if len(datetime_cols) > 0:
            insights["data_characteristics"].append("Time series dataset detected")
            insights["suggested_visualizations"].extend([
                "Line chart for trends over time",
                "Area chart for cumulative metrics",
                "Time series decomposition"
            ])
            insights["recommendations"].append("Consider time-based aggregations (daily, monthly, yearly)")
        
        if numeric_ratio > 0.7:
            insights["data_characteristics"].append("Highly numeric dataset")
            insights["suggested_visualizations"].extend([
                "Correlation heatmap",
                "Scatter plot matrix",
                "Box plots for distribution analysis"
            ])
            insights["recommendations"].append("Suitable for statistical analysis and machine learning")
        
        # Check for categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            insights["data_characteristics"].append(f"{len(categorical_cols)} categorical columns found")
            insights["suggested_visualizations"].extend([
                "Bar charts for category comparisons",
                "Pie charts for composition",
                "Stacked bar charts for multi-category analysis"
            ])
        
        # Dataset size recommendations
        if len(df) > 10000:
            insights["recommendations"].append("Large dataset: Consider sampling for initial visualizations")
        
        if len(df.columns) > 20:
            insights["recommendations"].append("Many columns: Consider feature selection or dimensionality reduction")
        
        return insights
