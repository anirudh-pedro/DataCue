"""
Chart Recommendation Engine
Rule-based system to suggest optimal chart types based on data characteristics
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ChartRecommendationEngine:
    """
    Intelligent chart recommendation system
    Analyzes column types, cardinality, and relationships to suggest best visualizations
    """
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> List[Dict[str, Any]]:
        """
        Initialize rule-based recommendation system
        """
        return [
            # Single column rules
            {
                "name": "numeric_distribution",
                "condition": lambda col_type, cardinality, **kwargs: (
                    col_type in ['numeric', 'integer', 'float'] and cardinality > 10
                ),
                "recommended_charts": ["histogram", "box_plot"],
                "priority": 10,
                "description": "Numeric column with many unique values → distribution charts"
            },
            {
                "name": "categorical_low_cardinality",
                "condition": lambda col_type, cardinality, **kwargs: (
                    col_type in ['categorical', 'string', 'object'] and cardinality <= 10
                ),
                "recommended_charts": ["bar_chart", "pie_chart"],
                "priority": 10,
                "description": "Categorical with few values → bar/pie chart"
            },
            {
                "name": "categorical_medium_cardinality",
                "condition": lambda col_type, cardinality, **kwargs: (
                    col_type in ['categorical', 'string', 'object'] and 10 < cardinality <= 50
                ),
                "recommended_charts": ["bar_chart"],
                "priority": 8,
                "description": "Categorical with moderate values → bar chart"
            },
            {
                "name": "time_series",
                "condition": lambda col_type, is_time, **kwargs: (
                    is_time or col_type in ['datetime', 'date']
                ),
                "recommended_charts": ["line_chart", "time_series"],
                "priority": 15,
                "description": "Time/date column → time series"
            },
            
            # Two column rules
            {
                "name": "numeric_vs_numeric",
                "condition": lambda x_type, y_type, **kwargs: (
                    x_type in ['numeric', 'integer', 'float'] and 
                    y_type in ['numeric', 'integer', 'float']
                ),
                "recommended_charts": ["scatter", "line_chart"],
                "priority": 12,
                "description": "Two numeric columns → scatter plot"
            },
            {
                "name": "categorical_vs_numeric",
                "condition": lambda x_type, y_type, x_cardinality, **kwargs: (
                    x_type in ['categorical', 'string', 'object'] and 
                    y_type in ['numeric', 'integer', 'float'] and
                    x_cardinality <= 20
                ),
                "recommended_charts": ["grouped_bar", "box_plot"],
                "priority": 11,
                "description": "Category vs numeric → grouped bar/box plot"
            },
            {
                "name": "time_vs_numeric",
                "condition": lambda x_type, y_type, x_is_time, **kwargs: (
                    (x_is_time or x_type in ['datetime', 'date']) and 
                    y_type in ['numeric', 'integer', 'float']
                ),
                "recommended_charts": ["time_series", "line_chart"],
                "priority": 13,
                "description": "Time vs numeric → time series"
            }
        ]
    
    def recommend_for_single_column(
        self, 
        column_name: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Recommend chart types for a single column
        
        Returns:
            List of recommendations with chart type, confidence, and reasoning
        """
        recommendations = []
        
        col_type = self._normalize_type(metadata.get('type', 'unknown'))
        cardinality = metadata.get('unique_count', 0)
        is_time = metadata.get('is_time_series', False)
        
        for rule in self.rules:
            # Skip multi-column rules
            if any(param in rule['condition'].__code__.co_varnames 
                   for param in ['x_type', 'y_type', 'x_cardinality', 'y_cardinality']):
                continue
            
            try:
                if rule['condition'](
                    col_type=col_type,
                    cardinality=cardinality,
                    is_time=is_time
                ):
                    for chart_type in rule['recommended_charts']:
                        recommendations.append({
                            "chart_type": chart_type,
                            "column": column_name,
                            "confidence": self._calculate_confidence(rule, metadata),
                            "reason": rule['description'],
                            "priority": rule['priority']
                        })
            except Exception as e:
                logger.debug(f"Rule '{rule['name']}' evaluation failed: {str(e)}")
                continue
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda x: (x['priority'], x['confidence']), reverse=True)
        
        return recommendations
    
    def recommend_for_column_pair(
        self,
        x_column: str,
        y_column: str,
        x_metadata: Dict[str, Any],
        y_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Recommend chart types for a pair of columns
        
        Returns:
            List of recommendations with chart type, confidence, and reasoning
        """
        recommendations = []
        
        x_type = self._normalize_type(x_metadata.get('type', 'unknown'))
        y_type = self._normalize_type(y_metadata.get('type', 'unknown'))
        x_cardinality = x_metadata.get('unique_count', 0)
        y_cardinality = y_metadata.get('unique_count', 0)
        x_is_time = x_metadata.get('is_time_series', False)
        y_is_time = y_metadata.get('is_time_series', False)
        
        for rule in self.rules:
            # Skip single-column rules
            if not any(param in rule['condition'].__code__.co_varnames 
                      for param in ['x_type', 'y_type']):
                continue
            
            try:
                if rule['condition'](
                    x_type=x_type,
                    y_type=y_type,
                    x_cardinality=x_cardinality,
                    y_cardinality=y_cardinality,
                    x_is_time=x_is_time,
                    y_is_time=y_is_time
                ):
                    for chart_type in rule['recommended_charts']:
                        recommendations.append({
                            "chart_type": chart_type,
                            "columns": {"x": x_column, "y": y_column},
                            "confidence": self._calculate_confidence_pair(
                                rule, x_metadata, y_metadata
                            ),
                            "reason": rule['description'],
                            "priority": rule['priority']
                        })
            except Exception as e:
                logger.debug(f"Rule '{rule['name']}' evaluation failed: {str(e)}")
                continue
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda x: (x['priority'], x['confidence']), reverse=True)
        
        return recommendations
    
    def recommend_dashboard_charts(
        self,
        columns_metadata: Dict[str, Dict[str, Any]],
        max_charts: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend complete set of charts for dashboard
        Balances different chart types and column coverage
        """
        all_recommendations = []
        
        # Get column names by type
        numeric_cols = []
        categorical_cols = []
        time_cols = []
        
        for col_name, meta in columns_metadata.items():
            col_type = self._normalize_type(meta.get('type', 'unknown'))
            if col_type in ['numeric', 'integer', 'float']:
                numeric_cols.append(col_name)
            elif col_type in ['categorical', 'string', 'object']:
                categorical_cols.append(col_name)
            if meta.get('is_time_series', False):
                time_cols.append(col_name)
        
        # Priority 1: Single column charts (distributions)
        for col_name, meta in list(columns_metadata.items())[:5]:  # Limit to first 5
            recs = self.recommend_for_single_column(col_name, meta)
            if recs:
                all_recommendations.append(recs[0])  # Take best recommendation
        
        # Priority 2: Time series (if available)
        if time_cols and numeric_cols:
            time_col = time_cols[0]
            for num_col in numeric_cols[:2]:  # Top 2 numeric columns
                recs = self.recommend_for_column_pair(
                    time_col, num_col,
                    columns_metadata[time_col],
                    columns_metadata[num_col]
                )
                if recs:
                    all_recommendations.append(recs[0])
        
        # Priority 3: Scatter plots (numeric vs numeric)
        for i, x_col in enumerate(numeric_cols[:3]):
            for y_col in numeric_cols[i+1:4]:
                recs = self.recommend_for_column_pair(
                    x_col, y_col,
                    columns_metadata[x_col],
                    columns_metadata[y_col]
                )
                if recs and recs[0]['chart_type'] == 'scatter':
                    all_recommendations.append(recs[0])
        
        # Priority 4: Category vs measure
        for cat_col in categorical_cols[:2]:
            for num_col in numeric_cols[:2]:
                recs = self.recommend_for_column_pair(
                    cat_col, num_col,
                    columns_metadata[cat_col],
                    columns_metadata[num_col]
                )
                if recs:
                    all_recommendations.append(recs[0])
        
        # Deduplicate and limit
        seen = set()
        unique_recs = []
        for rec in all_recommendations:
            key = (rec['chart_type'], str(rec.get('column', rec.get('columns', ''))))
            if key not in seen:
                seen.add(key)
                unique_recs.append(rec)
        
        # Sort by priority and return top N
        unique_recs.sort(key=lambda x: x['priority'], reverse=True)
        return unique_recs[:max_charts]
    
    def _normalize_type(self, type_str: str) -> str:
        """
        Normalize column type to standard categories
        """
        type_str = str(type_str).lower()
        
        if any(t in type_str for t in ['int', 'float', 'number', 'numeric']):
            return 'numeric'
        elif any(t in type_str for t in ['object', 'string', 'str', 'category']):
            return 'categorical'
        elif any(t in type_str for t in ['datetime', 'date', 'time', 'timestamp']):
            return 'datetime'
        else:
            return 'unknown'
    
    def _calculate_confidence(self, rule: Dict[str, Any], metadata: Dict[str, Any]) -> float:
        """
        Calculate confidence score (0-1) for a recommendation
        """
        base_confidence = 0.7
        
        # Boost confidence for clear patterns
        cardinality = metadata.get('unique_count', 0)
        total_rows = metadata.get('total_rows', cardinality)
        
        if total_rows > 0:
            uniqueness_ratio = cardinality / total_rows
            
            # High uniqueness for numeric → distribution charts
            if rule['name'] == 'numeric_distribution' and uniqueness_ratio > 0.5:
                base_confidence += 0.2
            
            # Low uniqueness for categorical → bar/pie charts
            if rule['name'] == 'categorical_low_cardinality' and uniqueness_ratio < 0.1:
                base_confidence += 0.2
        
        return min(base_confidence, 1.0)
    
    def _calculate_confidence_pair(
        self, 
        rule: Dict[str, Any],
        x_metadata: Dict[str, Any],
        y_metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence for column pair recommendation
        """
        base_confidence = 0.75
        
        # Boost for time series
        if rule['name'] == 'time_vs_numeric':
            base_confidence += 0.15
        
        # Boost for strong correlations (if available)
        if rule['name'] == 'numeric_vs_numeric':
            correlation = abs(y_metadata.get('correlation_with', {}).get(x_metadata.get('name', ''), 0))
            if correlation > 0.5:
                base_confidence += 0.15
        
        return min(base_confidence, 1.0)
