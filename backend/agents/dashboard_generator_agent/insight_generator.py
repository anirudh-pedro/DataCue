"""
Insight Generator
Auto-generates natural language narratives for charts
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class InsightGenerator:
    """
    Generates AI-powered natural language insights for charts
    Uses statistical analysis and pattern recognition
    """
    
    def __init__(self):
        self.insight_templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, List[str]]:
        """
        Initialize narrative templates for different chart types and patterns
        """
        return {
            "histogram": {
                "normal": "The distribution of {column} is approximately normal with a mean of {mean:.2f}.",
                "skewed_right": "The distribution of {column} is right-skewed, with most values concentrated below {median:.2f}.",
                "skewed_left": "The distribution of {column} is left-skewed, with most values concentrated above {median:.2f}.",
                "outliers": "Notable outliers detected in {column}, with values ranging from {min:.2f} to {max:.2f}.",
                "bimodal": "The distribution shows multiple peaks, suggesting distinct subgroups in the data."
            },
            "scatter": {
                "strong_positive": "Strong positive correlation ({corr:.2f}) between {x} and {y} - as {x} increases, {y} tends to increase significantly.",
                "strong_negative": "Strong negative correlation ({corr:.2f}) between {x} and {y} - as {x} increases, {y} tends to decrease significantly.",
                "moderate": "Moderate correlation ({corr:.2f}) between {x} and {y}, suggesting some relationship but with considerable variation.",
                "weak": "Weak correlation ({corr:.2f}) between {x} and {y} - the variables show minimal linear relationship.",
                "no_correlation": "No significant correlation ({corr:.2f}) between {x} and {y} - the variables appear independent."
            },
            "time_series": {
                "increasing": "{column} shows an overall increasing trend over time, growing by {change:.1f}% from {start_date} to {end_date}.",
                "decreasing": "{column} shows an overall decreasing trend over time, declining by {change:.1f}% from {start_date} to {end_date}.",
                "stable": "{column} remains relatively stable over time, with minimal variation around {mean:.2f}.",
                "seasonal": "Clear seasonal patterns detected in {column}, with regular fluctuations throughout the period.",
                "volatile": "{column} exhibits high volatility with frequent sharp changes, suggesting unpredictable behavior."
            },
            "bar": {
                "dominant": "'{top_category}' dominates with {top_count} occurrences ({percentage:.1f}% of total).",
                "balanced": "The distribution across categories is relatively balanced, with no single dominant category.",
                "concentrated": "Top {n} categories account for {percentage:.1f}% of all data, showing high concentration.",
                "diverse": "Highly diverse distribution across {total} categories with relatively even spread."
            },
            "kpi": {
                "high": "{metric} is {value:.2f}, which is {comparison} the typical range.",
                "trend_up": "{metric} is trending upward, showing {change:.1f}% growth.",
                "trend_down": "{metric} is trending downward, showing {change:.1f}% decline.",
                "stable": "{metric} remains stable at {value:.2f}."
            }
        }
    
    def generate_insight(
        self,
        data: pd.DataFrame,
        chart_type: str,
        columns: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate narrative insights for a chart
        
        Args:
            data: The dataframe
            chart_type: Type of chart
            columns: Dictionary with column mappings
            **kwargs: Additional parameters (for backwards compatibility)
            
        Returns:
            Dictionary with narrative, key_findings, and recommendations
        """
        # Normalize column info - accept either columns dict or kwargs
        chart_config = columns or kwargs
        
        try:
            if chart_type == "histogram":
                return self._generate_histogram_insight(data, chart_config)
            elif chart_type == "scatter":
                return self._generate_scatter_insight(data, chart_config)
            elif chart_type in ["line", "time_series"]:
                return self._generate_timeseries_insight(data, chart_config)
            elif chart_type == "bar":
                return self._generate_bar_insight(data, chart_config)
            elif chart_type == "grouped_bar":
                return self._generate_grouped_bar_insight(data, chart_config)
            elif chart_type == "kpi":
                return self._generate_kpi_insight(data, chart_config)
            elif chart_type == "pie":
                return self._generate_pie_insight(data, chart_config)
            elif chart_type == "heatmap":
                return self._generate_heatmap_insight(data, chart_config)
            elif chart_type in ["treemap", "funnel", "sankey", "stacked_area"]:
                return self._generate_advanced_chart_insight(data, chart_type, chart_config)
            else:
                return self._generate_default_insight(data, chart_config)
                
        except Exception as e:
            logger.error(f"Error generating insight for {data}: {str(e)}")
            return {
                "narrative": "Analysis of data...",
                "key_findings": [],
                "recommendations": [],
                "pattern": "N/A"
            }
    
    def _generate_histogram_insight(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for histogram"""
        column = config.get('column')
        if not column or column not in data.columns:
            return self._generate_default_insight(data, config)
        
        values = data[column].dropna()
        
        if len(values) == 0:
            return self._generate_default_insight(data, config)
        
        mean_val = values.mean()
        median_val = values.median()
        std_val = values.std()
        skewness = values.skew()
        
        # Determine distribution type
        if abs(skewness) < 0.5:
            pattern = "normal"
        elif skewness > 0.5:
            pattern = "skewed_right"
        else:
            pattern = "skewed_left"
        
        # Generate narrative
        template = self.insight_templates["histogram"][pattern]
        narrative = template.format(
            column=str(column).replace('_', ' ').title(),
            mean=mean_val,
            median=median_val
        )
        
        # Key findings
        findings = [
            f"Mean: {mean_val:.2f}, Median: {median_val:.2f}, Std Dev: {std_val:.2f}",
            f"Range: {values.min():.2f} to {values.max():.2f}"
        ]
        
        # Detect outliers using IQR method
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        outliers = values[(values < Q1 - 1.5 * IQR) | (values > Q3 + 1.5 * IQR)]
        
        if len(outliers) > 0:
            findings.append(f"{len(outliers)} outliers detected ({len(outliers)/len(values)*100:.1f}% of data)")
        
        # Recommendations
        recommendations = []
        if len(outliers) > len(values) * 0.05:
            recommendations.append("Consider investigating outliers - they may represent data errors or important edge cases")
        
        if std_val > mean_val:
            recommendations.append("High variability detected - consider segmenting data for more detailed analysis")
        
        return {
            "narrative": narrative,
            "key_findings": findings,
            "recommendations": recommendations,
            "pattern": pattern
        }
    
    def _generate_scatter_insight(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for scatter plot"""
        columns = config.get('columns', {})
        x_col = columns.get('x')
        y_col = columns.get('y')
        
        insights_data = config.get('insights', {})
        corr = insights_data.get('correlation', 0)
        
        # Determine correlation strength
        abs_corr = abs(corr)
        if abs_corr > 0.7:
            if corr > 0:
                pattern = "strong_positive"
            else:
                pattern = "strong_negative"
        elif abs_corr > 0.4:
            pattern = "moderate"
        elif abs_corr > 0.2:
            pattern = "weak"
        else:
            pattern = "no_correlation"
        
        # Generate narrative
        template = self.insight_templates["scatter"][pattern]
        narrative = template.format(
            x=x_col.replace('_', ' ').title(),
            y=y_col.replace('_', ' ').title(),
            corr=corr
        )
        
        # Key findings
        findings = [
            f"Correlation coefficient: {corr:.3f}",
            f"Relationship strength: {insights_data.get('correlation_strength', 'unknown')}",
            f"Direction: {insights_data.get('correlation_direction', 'unknown')}"
        ]
        
        # Recommendations
        recommendations = []
        if abs_corr > 0.7:
            recommendations.append(f"Strong relationship detected - {y_col} can be predicted from {x_col} with good accuracy")
        elif abs_corr > 0.4:
            recommendations.append(f"Moderate relationship - consider additional variables to improve predictions")
        else:
            recommendations.append(f"Weak or no linear relationship - explore non-linear patterns or other variables")
        
        return {
            "narrative": narrative,
            "key_findings": findings,
            "recommendations": recommendations,
            "pattern": pattern
        }
    
    def _generate_timeseries_insight(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for time series"""
        columns = config.get('columns', {})
        value_col = columns.get('value')
        time_col = columns.get('time')
        
        insights_data = config.get('insights', {})
        
        # Calculate trend
        values = data[value_col].dropna()
        start_val = values.iloc[0]
        end_val = values.iloc[-1]
        change_pct = ((end_val - start_val) / start_val) * 100 if start_val != 0 else 0
        
        # Determine pattern
        if abs(change_pct) < 5:
            pattern = "stable"
        elif change_pct > 5:
            pattern = "increasing"
        else:
            pattern = "decreasing"
        
        # Check volatility
        volatility = values.std() / values.mean() if values.mean() != 0 else 0
        if volatility > 0.3:
            pattern = "volatile"
        
        # Generate narrative
        template = self.insight_templates["time_series"][pattern]
        narrative = template.format(
            column=value_col.replace('_', ' ').title(),
            change=abs(change_pct),
            start_date=insights_data.get('start_date', 'start'),
            end_date=insights_data.get('end_date', 'end'),
            mean=values.mean()
        )
        
        # Key findings
        findings = [
            f"Overall change: {change_pct:+.1f}%",
            f"Average value: {values.mean():.2f}",
            f"Volatility: {volatility:.2%}"
        ]
        
        # Recommendations
        recommendations = []
        if pattern == "increasing":
            recommendations.append("Positive trend - monitor for sustainability and potential saturation points")
        elif pattern == "decreasing":
            recommendations.append("Declining trend - investigate root causes and potential interventions")
        elif pattern == "volatile":
            recommendations.append("High volatility - consider smoothing techniques or identifying cyclical patterns")
        
        return {
            "narrative": narrative,
            "key_findings": findings,
            "recommendations": recommendations,
            "pattern": pattern
        }
    
    def _generate_bar_insight(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for bar chart"""
        column = config.get('column')
        insights_data = config.get('insights', {})
        
        top_value = insights_data.get('top_value', 'N/A')
        top_count = insights_data.get('top_count', 0)
        total_unique = insights_data.get('total_unique', 0)
        
        total_count = len(data[column])
        top_percentage = (top_count / total_count * 100) if total_count > 0 else 0
        
        # Determine pattern
        if top_percentage > 50:
            pattern = "dominant"
        elif total_unique > 10 and top_percentage < 20:
            pattern = "diverse"
        elif top_percentage > 30:
            pattern = "concentrated"
        else:
            pattern = "balanced"
        
        # Generate narrative
        template = self.insight_templates["bar"][pattern]
        narrative = template.format(
            top_category=top_value,
            top_count=top_count,
            percentage=top_percentage,
            n=3,
            total=total_unique
        )
        
        # Key findings
        findings = [
            f"Most common: '{top_value}' ({top_count} occurrences)",
            f"Total categories: {total_unique}",
            f"Distribution pattern: {pattern}"
        ]
        
        # Recommendations
        recommendations = []
        if pattern == "dominant":
            recommendations.append(f"Single category dominates - consider focusing resources on '{top_value}'")
        elif pattern == "diverse":
            recommendations.append("High diversity - segment analysis or grouping may provide clearer insights")
        
        return {
            "narrative": narrative,
            "key_findings": findings,
            "recommendations": recommendations,
            "pattern": pattern
        }
    
    def _generate_grouped_bar_insight(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for grouped bar chart"""
        columns = config.get('columns', {})
        category_col = columns.get('category')
        value_col = columns.get('value')
        
        insights_data = config.get('insights', {})
        top_category = insights_data.get('top_category', 'N/A')
        max_value = insights_data.get('max_value', 0)
        
        narrative = f"'{top_category}' leads in {value_col.replace('_', ' ')} with a total of {max_value:.2f}. "
        narrative += f"Comparison across {category_col.replace('_', ' ')} shows varying performance levels."
        
        findings = [
            f"Top performer: '{top_category}' ({max_value:.2f})",
            f"Categories analyzed: {insights_data.get('categories_count', 0)}"
        ]
        
        return {
            "narrative": narrative,
            "key_findings": findings,
            "recommendations": [
                f"Analyze success factors of '{top_category}' for potential replication",
                "Investigate underperforming categories for improvement opportunities"
            ],
            "pattern": "comparative"
        }
    
    def _generate_kpi_insight(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for KPI card"""
        kpi_data = config.get('data', {})
        value = kpi_data.get('primary_value', 0)
        avg = kpi_data.get('average', value)
        
        narrative = f"Current value is {value:.2f} with an average of {avg:.2f} across the dataset."
        
        return {
            "narrative": narrative,
            "key_findings": [
                f"Total: {value:.2f}",
                f"Average: {avg:.2f}",
                f"Max: {kpi_data.get('max', 0):.2f}"
            ],
            "recommendations": [],
            "pattern": "summary"
        }
    
    def _generate_pie_insight(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for pie chart"""
        insights_data = config.get('insights', {})
        dominant = insights_data.get('dominant_category', 'N/A')
        percentage = insights_data.get('dominant_percentage', 0)
        
        narrative = f"'{dominant}' represents the largest share at {percentage:.1f}% of the total."
        
        return {
            "narrative": narrative,
            "key_findings": [f"Dominant category: '{dominant}' ({percentage:.1f}%)"],
            "recommendations": [],
            "pattern": "proportional"
        }
    
    def _generate_heatmap_insight(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for correlation heatmap"""
        insights_data = config.get('insights', {})
        strong_corrs = insights_data.get('strong_correlations', [])
        
        if strong_corrs:
            narrative = f"Analysis reveals {len(strong_corrs)} strong correlation(s) between variables. "
            narrative += "These relationships may indicate important dependencies in the data."
        else:
            narrative = "No strong correlations detected - variables appear relatively independent."
        
        findings = [f"{len(strong_corrs)} strong correlations found"]
        for corr in strong_corrs[:3]:  # Top 3
            findings.append(f"{corr.get('column1', '')} ↔ {corr.get('column2', '')}: {corr.get('correlation', 0):.2f}")
        
        return {
            "narrative": narrative,
            "key_findings": findings,
            "recommendations": [
                "Investigate strong correlations for causal relationships",
                "Consider feature selection based on correlation patterns"
            ],
            "pattern": "correlation"
        }
    
    def _generate_advanced_chart_insight(
        self,
        data: pd.DataFrame,
        chart_type: str,
        chart_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for advanced chart types (treemap, funnel, sankey, stacked_area)"""
        try:
            if chart_type == "treemap":
                category_col = chart_config.get('category_column')
                value_col = chart_config.get('value_column')
                
                if category_col and value_col:
                    grouped = data.groupby(category_col)[value_col].sum().sort_values(ascending=False)
                    top_cat = grouped.index[0]
                    top_val = grouped.iloc[0]
                    total = grouped.sum()
                    
                    return {
                        "narrative": f"'{top_cat}' represents the largest segment with {top_val:.2f} ({top_val/total*100:.1f}% of total). The hierarchy shows {len(grouped)} distinct categories.",
                        "key_findings": [f"Top category: {top_cat}", f"Total categories: {len(grouped)}"],
                        "recommendations": ["Focus on top-performing segments", "Investigate smaller categories for growth potential"],
                        "pattern": "hierarchical"
                    }
            
            elif chart_type == "funnel":
                stage_col = chart_config.get('stage_column')
                value_col = chart_config.get('value_column')
                
                if stage_col and value_col:
                    stages = data.sort_values(value_col, ascending=False)
                    conversion_rate = (stages[value_col].iloc[-1] / stages[value_col].iloc[0]) * 100
                    
                    return {
                        "narrative": f"The funnel shows {len(stages)} stages with an overall conversion rate of {conversion_rate:.1f}%. Largest drop occurs between stages.",
                        "key_findings": [f"Overall conversion: {conversion_rate:.1f}%", f"Total stages: {len(stages)}"],
                        "recommendations": ["Identify and optimize bottleneck stages", "Improve conversion at critical drop-off points"],
                        "pattern": "conversion"
                    }
            
            elif chart_type == "sankey":
                return {
                    "narrative": f"The flow diagram visualizes {len(data)} connections between nodes, showing the movement and distribution of values across the system.",
                    "key_findings": [f"Total flows: {len(data)}"],
                    "recommendations": ["Analyze high-volume flows for optimization", "Investigate unexpected flow patterns"],
                    "pattern": "flow"
                }
            
            elif chart_type == "stacked_area":
                time_col = chart_config.get('time_column')
                category_col = chart_config.get('category_column')
                
                if time_col and category_col:
                    categories = data[category_col].nunique()
                    
                    return {
                        "narrative": f"The composition shows how {categories} categories evolve over time. The stacked view reveals changing proportions and total volume trends.",
                        "key_findings": [f"Categories tracked: {categories}"],
                        "recommendations": ["Monitor category share changes over time", "Identify growing and declining segments"],
                        "pattern": "composition"
                    }
            
            # Default fallback
            return {
                "narrative": f"This {chart_type} visualization provides insights into the data structure and patterns.",
                "key_findings": [f"Chart type: {chart_type}"],
                "recommendations": ["Explore interactive features for deeper insights"],
                "pattern": "general"
            }
            
        except Exception as e:
            logger.error(f"Error generating advanced chart insight: {str(e)}")
            return {
                "narrative": f"Analysis of {chart_type} data",
                "key_findings": [],
                "recommendations": [],
                "pattern": "general"
            }

    def _generate_default_insight(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Default insight for unknown chart types"""
        return {
            "narrative": f"Analysis of {config.get('title', 'data visualization')}.",
            "key_findings": ["Visual representation of data patterns"],
            "recommendations": [],
            "pattern": "general"
        }
