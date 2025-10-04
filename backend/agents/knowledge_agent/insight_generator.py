"""
Insight Generator Module
Uses LLM (Groq API) + Statistical Analysis to generate human-like insights
from data profiling results.
"""

import json
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime


class InsightGenerator:
    """
    Generates natural language insights from statistical data profiles
    using LLM reasoning combined with statistical analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Insight Generator.
        
        Args:
            api_key: Groq API key (if None, will need to be set later)
        """
        self.api_key = api_key
        self.groq_client = None
        
        # Initialize Groq client if API key provided
        if api_key:
            self._initialize_groq_client()
    
    def set_api_key(self, api_key: str):
        """Set the Groq API key and initialize client"""
        self.api_key = api_key
        self._initialize_groq_client()
    
    def _initialize_groq_client(self):
        """Initialize the Groq client"""
        try:
            from groq import Groq
            self.groq_client = Groq(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "Groq library not installed. Install with: pip install groq"
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Groq client: {str(e)}")
    
    def generate_insights(
        self, 
        profile_data: Dict[str, Any],
        data: pd.DataFrame,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights from profiled data.
        
        Args:
            profile_data: Output from DataProfiler.profile_dataset()
            data: Original DataFrame
            focus_areas: Specific areas to focus on (optional)
            
        Returns:
            Dictionary containing various insights
        """
        insights = {
            'executive_summary': self._generate_executive_summary(profile_data, data),
            'numeric_insights': self._generate_numeric_insights(profile_data),
            'categorical_insights': self._generate_categorical_insights(profile_data),
            'temporal_insights': self._generate_temporal_insights(profile_data),
            'correlation_insights': self._generate_correlation_insights(profile_data),
            'outlier_insights': self._generate_outlier_insights(profile_data),
            'missing_data_insights': self._generate_missing_data_insights(profile_data),
            'key_findings': self._extract_key_findings(profile_data),
            'recommendations': self._generate_recommendations(profile_data),
            'anomalies': self._detect_anomalies(profile_data, data)
        }
        
        # If LLM is available, enhance with LLM-generated insights
        if self.groq_client:
            insights['llm_narrative'] = self._generate_llm_narrative(profile_data, insights)
        else:
            insights['llm_narrative'] = "LLM not configured. Set API key to enable AI-powered narratives."
        
        return insights
    
    def _generate_executive_summary(
        self, 
        profile_data: Dict[str, Any],
        data: pd.DataFrame
    ) -> str:
        """Generate executive summary of the dataset"""
        basic = profile_data['basic_info']
        quality = profile_data['data_quality']
        
        summary = f"""
This dataset contains {basic['num_rows']:,} rows and {basic['num_columns']} columns, 
occupying {basic['memory_usage_mb']:.2f} MB of memory. The overall data quality score is 
{quality['overall_quality_score']:.1f}/100 ({quality['quality_grade']}). 
"""
        
        if basic['duplicate_rows'] > 0:
            summary += f"There are {basic['duplicate_rows']} duplicate rows. "
        
        if basic['missing_percentage'] > 5:
            summary += f"Missing data accounts for {basic['missing_percentage']:.1f}% of total values. "
        
        # Add column type distribution
        col_types = basic['column_types']
        summary += f"\n\nColumn types: "
        type_descriptions = []
        for dtype, count in col_types.items():
            type_descriptions.append(f"{count} {str(dtype)}")
        summary += ", ".join(type_descriptions) + "."
        
        return summary.strip()
    
    def _generate_numeric_insights(self, profile_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate insights for numeric columns"""
        insights = []
        numeric_profile = profile_data.get('numeric_profile', {})
        
        if not numeric_profile:
            return [{"insight": "No numeric columns found in the dataset.", "type": "info"}]
        
        # Identify most and least varying columns
        variations = []
        for col, stats in numeric_profile.items():
            if stats['coefficient_of_variation'] > 0:
                variations.append((col, stats['coefficient_of_variation']))
        
        if variations:
            variations.sort(key=lambda x: x[1], reverse=True)
            most_varying = variations[0]
            least_varying = variations[-1]
            
            insights.append({
                "column": most_varying[0],
                "insight": f"'{most_varying[0]}' shows the highest variation (CV: {most_varying[1]:.1f}%), indicating significant spread in values.",
                "type": "variation",
                "severity": "high"
            })
            
            insights.append({
                "column": least_varying[0],
                "insight": f"'{least_varying[0]}' shows minimal variation (CV: {least_varying[1]:.1f}%), suggesting relatively stable values.",
                "type": "variation",
                "severity": "low"
            })
        
        # Identify skewed distributions
        for col, stats in numeric_profile.items():
            if abs(stats['skewness']) > 1:
                direction = "right" if stats['skewness'] > 0 else "left"
                insights.append({
                    "column": col,
                    "insight": f"'{col}' is heavily {direction}-skewed (skewness: {stats['skewness']:.2f}), indicating asymmetric distribution.",
                    "type": "distribution",
                    "severity": "medium"
                })
        
        # Identify columns with many zeros
        for col, stats in numeric_profile.items():
            if stats['zeros_pct'] > 30:
                insights.append({
                    "column": col,
                    "insight": f"'{col}' contains {stats['zeros_pct']:.1f}% zeros, which may indicate sparse data or special meaning of zero.",
                    "type": "zeros",
                    "severity": "medium"
                })
        
        # Identify binary numeric columns
        for col, stats in numeric_profile.items():
            if stats['is_binary']:
                insights.append({
                    "column": col,
                    "insight": f"'{col}' is binary (only 2 unique values: {stats['min']}, {stats['max']}), possibly a flag or indicator.",
                    "type": "binary",
                    "severity": "info"
                })
        
        # Identify constant columns
        for col, stats in numeric_profile.items():
            if stats['is_constant']:
                insights.append({
                    "column": col,
                    "insight": f"'{col}' has a constant value ({stats['mean']}). Consider removing this column.",
                    "type": "constant",
                    "severity": "warning"
                })
        
        return insights
    
    def _generate_categorical_insights(self, profile_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate insights for categorical columns"""
        insights = []
        cat_profile = profile_data.get('categorical_profile', {})
        
        if not cat_profile:
            return [{"insight": "No categorical columns found in the dataset.", "type": "info"}]
        
        for col, stats in cat_profile.items():
            # High cardinality warning
            if stats['cardinality'] == 'high':
                insights.append({
                    "column": col,
                    "insight": f"'{col}' has high cardinality ({stats['unique_values']} unique values). May need special encoding for ML.",
                    "type": "cardinality",
                    "severity": "warning"
                })
            
            # Dominant category
            if stats['most_common_pct'] > 80:
                insights.append({
                    "column": col,
                    "insight": f"'{col}' is dominated by '{stats['most_common']}' ({stats['most_common_pct']:.1f}%), indicating class imbalance.",
                    "type": "imbalance",
                    "severity": "high"
                })
            
            # Binary categorical
            if stats['is_binary']:
                insights.append({
                    "column": col,
                    "insight": f"'{col}' is binary with values: {list(stats['top_5_values'].keys())}. Potential target variable or flag.",
                    "type": "binary",
                    "severity": "info"
                })
            
            # Low entropy (little variation)
            if stats['entropy'] < 1.0 and stats['unique_values'] > 2:
                insights.append({
                    "column": col,
                    "insight": f"'{col}' has low entropy ({stats['entropy']:.2f}), indicating limited diversity in values.",
                    "type": "entropy",
                    "severity": "medium"
                })
        
        return insights
    
    def _generate_temporal_insights(self, profile_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate insights for datetime columns"""
        insights = []
        datetime_profile = profile_data.get('datetime_profile', {})
        
        if not datetime_profile:
            return [{"insight": "No datetime columns found in the dataset.", "type": "info"}]
        
        for col, stats in datetime_profile.items():
            # Date range
            insights.append({
                "column": col,
                "insight": f"'{col}' spans {stats['date_range_days']} days from {stats['min_date']} to {stats['max_date']}.",
                "type": "range",
                "severity": "info"
            })
            
            # Time component
            if stats['has_time_component']:
                insights.append({
                    "column": col,
                    "insight": f"'{col}' includes time-of-day information. Consider time-based analysis.",
                    "type": "temporal",
                    "severity": "info"
                })
            
            # Monthly patterns
            if stats.get('month_distribution'):
                month_counts = stats['month_distribution']
                max_month = max(month_counts, key=month_counts.get)
                min_month = min(month_counts, key=month_counts.get)
                
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                insights.append({
                    "column": col,
                    "insight": f"'{col}' shows seasonal patterns: peak in {month_names[max_month-1]}, low in {month_names[min_month-1]}.",
                    "type": "seasonality",
                    "severity": "medium"
                })
        
        return insights
    
    def _generate_correlation_insights(self, profile_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate insights about correlations"""
        insights = []
        corr_data = profile_data.get('correlations', {})
        strong_corrs = corr_data.get('strong_correlations', [])
        
        if not strong_corrs:
            return [{"insight": "No strong correlations detected between numeric variables.", "type": "info"}]
        
        # Group by strength
        very_strong = [c for c in strong_corrs if abs(c['pearson']) > 0.9]
        strong = [c for c in strong_corrs if 0.7 < abs(c['pearson']) <= 0.9]
        
        if very_strong:
            insights.append({
                "insight": f"Found {len(very_strong)} very strong correlations (|r| > 0.9). These variables may be redundant.",
                "type": "correlation",
                "severity": "high"
            })
        
        if strong:
            insights.append({
                "insight": f"Found {len(strong)} strong correlations (0.7 < |r| ≤ 0.9). Consider feature selection.",
                "type": "correlation",
                "severity": "medium"
            })
        
        # Highlight specific strong correlations
        for corr in strong_corrs[:3]:  # Top 3
            direction = "positive" if corr['pearson'] > 0 else "negative"
            insights.append({
                "variables": f"{corr['variable_1']} & {corr['variable_2']}",
                "insight": f"Strong {direction} correlation between '{corr['variable_1']}' and '{corr['variable_2']}' (r={corr['pearson']:.3f}).",
                "type": "correlation_pair",
                "severity": "info"
            })
        
        return insights
    
    def _generate_outlier_insights(self, profile_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate insights about outliers"""
        insights = []
        outlier_data = profile_data.get('outliers', {})
        
        if not outlier_data:
            return [{"insight": "No numeric columns to analyze for outliers.", "type": "info"}]
        
        # Find columns with significant outliers
        significant_outliers = []
        for col, stats in outlier_data.items():
            if stats['iqr_outlier_pct'] > 5:  # More than 5% outliers
                significant_outliers.append((col, stats['iqr_outlier_pct']))
        
        if significant_outliers:
            significant_outliers.sort(key=lambda x: x[1], reverse=True)
            for col, pct in significant_outliers[:5]:  # Top 5
                insights.append({
                    "column": col,
                    "insight": f"'{col}' contains {pct:.1f}% outliers (IQR method). Consider investigation or capping.",
                    "type": "outlier",
                    "severity": "high" if pct > 10 else "medium"
                })
        else:
            insights.append({
                "insight": "No significant outliers detected in numeric columns.",
                "type": "outlier",
                "severity": "info"
            })
        
        return insights
    
    def _generate_missing_data_insights(self, profile_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate insights about missing data"""
        insights = []
        missing_data = profile_data.get('missing_patterns', {})
        
        if missing_data['total_missing'] == 0:
            return [{"insight": "No missing values detected. Dataset is complete!", "type": "info", "severity": "positive"}]
        
        # Overall missing data
        insights.append({
            "insight": f"Dataset has {missing_data['total_missing']:,} missing values across {len(missing_data['columns_with_missing'])} columns.",
            "type": "missing",
            "severity": "high" if missing_data['total_missing'] > 1000 else "medium"
        })
        
        # Columns with high missing percentage
        high_missing = [(col, pct) for col, pct in missing_data['columns_with_missing_pct'].items() if pct > 50]
        if high_missing:
            for col, pct in high_missing[:5]:
                insights.append({
                    "column": col,
                    "insight": f"'{col}' is {pct:.1f}% missing. Consider imputation or removal.",
                    "type": "missing",
                    "severity": "high"
                })
        
        # Complete rows analysis
        if missing_data['complete_rows_pct'] < 50:
            insights.append({
                "insight": f"Only {missing_data['complete_rows_pct']:.1f}% of rows are complete. Missing data is widespread.",
                "type": "missing",
                "severity": "critical"
            })
        
        return insights
    
    def _extract_key_findings(self, profile_data: Dict[str, Any]) -> List[str]:
        """Extract top key findings from all analyses"""
        findings = []
        
        # Data quality finding
        quality = profile_data['data_quality']
        findings.append(f"Overall data quality: {quality['quality_grade']}")
        
        # Strong correlations
        num_correlations = profile_data['correlations']['num_strong_correlations']
        if num_correlations > 0:
            findings.append(f"Detected {num_correlations} strong variable correlations")
        
        # Potential targets
        targets = profile_data['key_variables']['potential_targets']
        if targets:
            findings.append(f"Identified {len(targets)} potential target variables for prediction")
        
        # High variance features
        high_var = profile_data['key_variables']['high_variance']
        if high_var:
            findings.append(f"Found {len(high_var)} high-variance features that may be informative")
        
        # Missing data
        missing = profile_data['missing_patterns']
        if missing['total_missing'] > 0:
            findings.append(f"{len(missing['columns_with_missing'])} columns contain missing values")
        
        return findings
    
    def _generate_recommendations(self, profile_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = profile_data['data_quality']['recommendations'].copy()
        
        # Add correlation-based recommendations
        strong_corrs = profile_data['correlations']['strong_correlations']
        if len(strong_corrs) > 10:
            recommendations.append("Many strong correlations detected - Apply feature selection to reduce multicollinearity")
        
        # Add target variable recommendations
        targets = profile_data['key_variables']['potential_targets']
        if targets:
            target_names = [t['column'] for t in targets[:3]]
            recommendations.append(f"Consider these as potential prediction targets: {', '.join(target_names)}")
        
        # Add outlier recommendations
        outliers = profile_data.get('outliers', {})
        cols_with_outliers = [col for col, stats in outliers.items() if stats.get('has_outliers', False)]
        if len(cols_with_outliers) > 5:
            recommendations.append(f"{len(cols_with_outliers)} columns have outliers - Consider robust scaling or outlier treatment")
        
        return recommendations
    
    def _detect_anomalies(self, profile_data: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, str]]:
        """Detect unusual patterns or anomalies in the data"""
        anomalies = []
        
        # Check for unexpected value ranges
        numeric_profile = profile_data.get('numeric_profile', {})
        for col, stats in numeric_profile.items():
            # Negative values in columns that shouldn't have them
            if 'age' in col.lower() or 'count' in col.lower() or 'price' in col.lower():
                if stats['min'] < 0:
                    anomalies.append({
                        "column": col,
                        "anomaly": f"'{col}' contains negative values (min: {stats['min']:.2f}), which may be unexpected.",
                        "type": "value_range"
                    })
            
            # Very high kurtosis (heavy tails)
            if abs(stats['kurtosis']) > 10:
                anomalies.append({
                    "column": col,
                    "anomaly": f"'{col}' has extreme kurtosis ({stats['kurtosis']:.2f}), indicating heavy-tailed distribution.",
                    "type": "distribution"
                })
        
        # Check for potential data entry errors
        cat_profile = profile_data.get('categorical_profile', {})
        for col, stats in cat_profile.items():
            # Very high number of unique values for categorical
            if stats['unique_values'] > 0.9 * profile_data['basic_info']['num_rows']:
                anomalies.append({
                    "column": col,
                    "anomaly": f"'{col}' has nearly unique values ({stats['unique_values']}). May be an ID or need cleaning.",
                    "type": "cardinality"
                })
        
        return anomalies
    
    def _generate_llm_narrative(
        self, 
        profile_data: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> str:
        """
        Generate a comprehensive narrative using Groq LLM.
        """
        if not self.groq_client:
            return "LLM client not initialized. Call set_api_key() first."
        
        try:
            # Prepare structured summary for LLM
            summary = {
                "basic_info": profile_data['basic_info'],
                "quality_score": profile_data['data_quality']['overall_quality_score'],
                "key_findings": insights['key_findings'],
                "top_insights": {
                    "numeric": insights['numeric_insights'][:3],
                    "categorical": insights['categorical_insights'][:3],
                    "correlations": insights['correlation_insights'][:3]
                },
                "recommendations": insights['recommendations'][:5]
            }
            
            prompt = f"""You are a data analyst reviewing a dataset. Based on the following statistical analysis, 
provide a comprehensive, professional narrative summary in 2-3 paragraphs. Focus on:
1. What's most interesting about this data
2. Key patterns and relationships
3. Potential concerns or opportunities
4. Recommended next steps

Analysis Summary:
{json.dumps(summary, indent=2)}

Write a clear, executive-level summary that a non-technical stakeholder would understand."""

            # Call Groq API
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",  # Fast and capable model
                messages=[
                    {"role": "system", "content": "You are an expert data analyst who explains complex data patterns in clear, actionable language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Failed to generate LLM narrative: {str(e)}"
    
    def answer_question(
        self,
        question: str,
        profile_data: Dict[str, Any],
        data: pd.DataFrame
    ) -> str:
        """
        Answer a specific question about the data using LLM + data analysis.
        
        Args:
            question: Natural language question
            profile_data: Profiling data
            data: Original DataFrame
            
        Returns:
            Answer as string
        """
        if not self.groq_client:
            return "LLM client not initialized. Call set_api_key() first."
        
        try:
            # Provide context to LLM
            context = {
                "columns": list(data.columns),
                "shape": data.shape,
                "dtypes": data.dtypes.astype(str).to_dict(),
                "sample_stats": {
                    col: {
                        "type": str(data[col].dtype),
                        "unique": int(data[col].nunique()),
                        "sample_values": data[col].dropna().head(3).tolist()
                    }
                    for col in data.columns[:10]  # Limit to first 10 columns
                }
            }
            
            prompt = f"""You are a data analyst. Answer this question about the dataset:

Question: {question}

Dataset Context:
- Shape: {context['shape']}
- Columns: {', '.join(context['columns'][:20])}
- Column types and samples: {json.dumps(context['sample_stats'], indent=2)}

Provide a clear, specific answer based on the available data."""

            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": "You are a helpful data analyst assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Failed to answer question: {str(e)}"
