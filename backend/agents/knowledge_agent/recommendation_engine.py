"""
Recommendation Engine Module
Suggests next analytical steps, visualizations, and predictive modeling approaches
based on data characteristics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional


class RecommendationEngine:
    """
    Analyzes data profile and generates actionable recommendations for:
    - Next analytical steps
    - Visualization strategies
    - Feature engineering
    - Predictive modeling targets
    - Data preprocessing steps
    """
    
    def __init__(self):
        """Initialize the Recommendation Engine"""
        self.recommendations = []
        
    def generate_recommendations(
        self,
        profile_data: Dict[str, Any],
        data: pd.DataFrame,
        insights: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate comprehensive recommendations based on data analysis.
        
        Args:
            profile_data: Output from DataProfiler
            data: Original DataFrame
            insights: Optional insights from InsightGenerator
            
        Returns:
            Dictionary categorizing recommendations
        """
        recommendations = {
            'visualization': self._recommend_visualizations(profile_data, data),
            'analysis': self._recommend_analyses(profile_data, data),
            'preprocessing': self._recommend_preprocessing(profile_data, data),
            'feature_engineering': self._recommend_feature_engineering(profile_data, data),
            'modeling': self._recommend_modeling_approaches(profile_data, data),
            'data_quality': self._recommend_data_quality_improvements(profile_data, data),
            'next_steps': self._recommend_next_steps(profile_data, insights)
        }
        
        return recommendations
    
    def _recommend_visualizations(
        self,
        profile_data: Dict[str, Any],
        data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Recommend specific visualizations based on data characteristics"""
        viz_recommendations = []
        
        numeric_cols = list(profile_data.get('numeric_profile', {}).keys())
        cat_cols = list(profile_data.get('categorical_profile', {}).keys())
        datetime_cols = list(profile_data.get('datetime_profile', {}).keys())
        
        # Correlation heatmap for multiple numeric columns
        if len(numeric_cols) >= 3:
            viz_recommendations.append({
                'type': 'heatmap',
                'priority': 'high',
                'title': 'Correlation Heatmap',
                'description': f'Visualize correlations among {len(numeric_cols)} numeric variables',
                'columns': numeric_cols,
                'reason': 'Multiple numeric columns present - correlation patterns should be examined'
            })
        
        # Scatter matrix for numeric relationships
        if 3 <= len(numeric_cols) <= 10:
            viz_recommendations.append({
                'type': 'scatter_matrix',
                'priority': 'high',
                'title': 'Pairwise Scatter Plots',
                'description': f'Explore relationships between {len(numeric_cols)} variables',
                'columns': numeric_cols,
                'reason': 'Ideal number of variables for pairwise comparison'
            })
        
        # Time series plots for datetime columns
        if datetime_cols and numeric_cols:
            for date_col in datetime_cols:
                for num_col in numeric_cols[:3]:  # Top 3 numeric columns
                    viz_recommendations.append({
                        'type': 'line_chart',
                        'priority': 'high',
                        'title': f'{num_col} over time',
                        'description': f'Trend analysis of {num_col} vs {date_col}',
                        'x_column': date_col,
                        'y_column': num_col,
                        'reason': 'Temporal data available - trend analysis recommended'
                    })
        
        # Box plots for outlier visualization
        outliers = profile_data.get('outliers', {})
        cols_with_outliers = [col for col, stats in outliers.items() 
                             if stats.get('has_outliers', False)]
        
        if cols_with_outliers:
            viz_recommendations.append({
                'type': 'box_plot',
                'priority': 'medium',
                'title': 'Outlier Detection Box Plots',
                'description': f'Visualize outliers in {len(cols_with_outliers)} columns',
                'columns': cols_with_outliers[:5],  # Limit to 5
                'reason': 'Outliers detected - visualization helps understand distribution'
            })
        
        # Bar charts for categorical variables
        for col, stats in profile_data.get('categorical_profile', {}).items():
            if stats['cardinality'] == 'low' and stats['unique_values'] <= 20:
                viz_recommendations.append({
                    'type': 'bar_chart',
                    'priority': 'medium',
                    'title': f'Distribution of {col}',
                    'description': f'Category counts for {col} ({stats["unique_values"]} categories)',
                    'column': col,
                    'reason': 'Low cardinality categorical - good for bar chart'
                })
        
        # Histograms for numeric distributions
        for col in numeric_cols[:5]:  # Top 5
            viz_recommendations.append({
                'type': 'histogram',
                'priority': 'low',
                'title': f'Distribution of {col}',
                'description': f'Understand the distribution shape of {col}',
                'column': col,
                'reason': 'Basic distribution visualization'
            })
        
        return viz_recommendations
    
    def _recommend_analyses(
        self,
        profile_data: Dict[str, Any],
        data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Recommend specific analyses to perform"""
        analyses = []
        
        # Segmentation analysis for high-variation columns
        high_var_cols = profile_data.get('key_variables', {}).get('high_variance', [])
        if high_var_cols:
            col_name = high_var_cols[0]['column']
            analyses.append({
                'type': 'segmentation',
                'priority': 'high',
                'description': f'Segment data by {col_name} to find distinct groups',
                'method': 'clustering',
                'columns': [col_name],
                'reason': 'High variance suggests natural segments may exist'
            })
        
        # Correlation analysis for strong correlations
        strong_corrs = profile_data.get('correlations', {}).get('strong_correlations', [])
        if len(strong_corrs) > 5:
            analyses.append({
                'type': 'dimensionality_reduction',
                'priority': 'high',
                'description': 'Apply PCA or feature selection to reduce correlated features',
                'method': 'PCA',
                'reason': f'{len(strong_corrs)} strong correlations - redundancy may exist'
            })
        
        # Time series analysis
        if profile_data.get('datetime_profile'):
            analyses.append({
                'type': 'time_series_analysis',
                'priority': 'high',
                'description': 'Analyze trends, seasonality, and patterns over time',
                'methods': ['trend_analysis', 'seasonality_detection', 'forecasting'],
                'reason': 'Temporal data present - time series methods applicable'
            })
        
        # Outlier analysis
        outliers = profile_data.get('outliers', {})
        cols_with_many_outliers = [
            col for col, stats in outliers.items() 
            if stats.get('iqr_outlier_pct', 0) > 10
        ]
        
        if cols_with_many_outliers:
            analyses.append({
                'type': 'outlier_investigation',
                'priority': 'medium',
                'description': f'Investigate outliers in {len(cols_with_many_outliers)} columns',
                'columns': cols_with_many_outliers,
                'methods': ['isolation_forest', 'local_outlier_factor'],
                'reason': 'Significant outliers detected - may indicate anomalies or data issues'
            })
        
        # Category imbalance analysis
        cat_profile = profile_data.get('categorical_profile', {})
        imbalanced_cats = [
            col for col, stats in cat_profile.items()
            if stats.get('most_common_pct', 0) > 80
        ]
        
        if imbalanced_cats:
            analyses.append({
                'type': 'imbalance_analysis',
                'priority': 'medium',
                'description': f'Address class imbalance in {len(imbalanced_cats)} categorical columns',
                'columns': imbalanced_cats,
                'methods': ['oversampling', 'undersampling', 'SMOTE'],
                'reason': 'Severe class imbalance detected'
            })
        
        return analyses
    
    def _recommend_preprocessing(
        self,
        profile_data: Dict[str, Any],
        data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Recommend preprocessing steps"""
        preprocessing = []
        
        # Missing data handling
        missing_data = profile_data.get('missing_patterns', {})
        if missing_data.get('total_missing', 0) > 0:
            cols_with_missing = missing_data.get('columns_with_missing_pct', {})
            
            high_missing = {k: v for k, v in cols_with_missing.items() if v > 50}
            moderate_missing = {k: v for k, v in cols_with_missing.items() if 10 < v <= 50}
            low_missing = {k: v for k, v in cols_with_missing.items() if v <= 10}
            
            if high_missing:
                preprocessing.append({
                    'step': 'remove_columns',
                    'priority': 'high',
                    'description': f'Consider removing {len(high_missing)} columns with >50% missing data',
                    'columns': list(high_missing.keys()),
                    'reason': 'Too much missing data to reliably impute'
                })
            
            if moderate_missing:
                preprocessing.append({
                    'step': 'imputation',
                    'priority': 'high',
                    'description': f'Impute missing values in {len(moderate_missing)} columns',
                    'columns': list(moderate_missing.keys()),
                    'methods': ['mean', 'median', 'mode', 'KNN', 'iterative'],
                    'reason': 'Moderate missing data - imputation feasible'
                })
            
            if low_missing:
                preprocessing.append({
                    'step': 'simple_imputation',
                    'priority': 'medium',
                    'description': f'Fill missing values in {len(low_missing)} columns',
                    'columns': list(low_missing.keys()),
                    'methods': ['forward_fill', 'backward_fill', 'mean'],
                    'reason': 'Low missing data - simple methods sufficient'
                })
        
        # Scaling for numeric columns
        numeric_profile = profile_data.get('numeric_profile', {})
        if numeric_profile:
            # Check for different scales
            ranges = [stats['range'] for stats in numeric_profile.values() if stats['range'] > 0]
            if ranges and (max(ranges) / min(ranges) > 100):
                preprocessing.append({
                    'step': 'scaling',
                    'priority': 'high',
                    'description': 'Normalize/standardize numeric features (wide range of scales detected)',
                    'methods': ['StandardScaler', 'MinMaxScaler', 'RobustScaler'],
                    'reason': 'Features have vastly different scales'
                })
        
        # Encoding for categorical columns
        cat_profile = profile_data.get('categorical_profile', {})
        if cat_profile:
            low_cardinality = [col for col, stats in cat_profile.items() 
                             if stats['cardinality'] == 'low']
            high_cardinality = [col for col, stats in cat_profile.items() 
                              if stats['cardinality'] == 'high']
            
            if low_cardinality:
                preprocessing.append({
                    'step': 'encoding',
                    'priority': 'high',
                    'description': f'Encode {len(low_cardinality)} low-cardinality categorical columns',
                    'columns': low_cardinality,
                    'methods': ['one_hot_encoding', 'label_encoding'],
                    'reason': 'Required for machine learning models'
                })
            
            if high_cardinality:
                preprocessing.append({
                    'step': 'encoding',
                    'priority': 'medium',
                    'description': f'Handle {len(high_cardinality)} high-cardinality columns carefully',
                    'columns': high_cardinality,
                    'methods': ['target_encoding', 'frequency_encoding', 'embedding'],
                    'reason': 'High cardinality requires special encoding techniques'
                })
        
        # Remove constant columns
        numeric_profile = profile_data.get('numeric_profile', {})
        cat_profile = profile_data.get('categorical_profile', {})
        
        constant_cols = []
        constant_cols.extend([col for col, stats in numeric_profile.items() if stats.get('is_constant', False)])
        constant_cols.extend([col for col, stats in cat_profile.items() if stats.get('is_constant', False)])
        
        if constant_cols:
            preprocessing.append({
                'step': 'remove_constants',
                'priority': 'high',
                'description': f'Remove {len(constant_cols)} constant columns (no variation)',
                'columns': constant_cols,
                'reason': 'Constant columns provide no information'
            })
        
        return preprocessing
    
    def _recommend_feature_engineering(
        self,
        profile_data: Dict[str, Any],
        data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Recommend feature engineering opportunities"""
        features = []
        
        # DateTime feature extraction
        datetime_cols = list(profile_data.get('datetime_profile', {}).keys())
        if datetime_cols:
            features.append({
                'technique': 'temporal_features',
                'priority': 'high',
                'description': f'Extract temporal features from {len(datetime_cols)} datetime columns',
                'columns': datetime_cols,
                'new_features': ['year', 'month', 'day', 'day_of_week', 'quarter', 'is_weekend', 'hour'],
                'reason': 'Temporal patterns often predictive'
            })
        
        # Interaction features for correlated variables
        strong_corrs = profile_data.get('correlations', {}).get('strong_correlations', [])
        if strong_corrs:
            features.append({
                'technique': 'interaction_features',
                'priority': 'medium',
                'description': 'Create interaction terms between correlated variables',
                'pairs': [(c['variable_1'], c['variable_2']) for c in strong_corrs[:5]],
                'operations': ['multiply', 'divide', 'add', 'subtract'],
                'reason': 'Strong correlations suggest meaningful interactions'
            })
        
        # Binning for high-variance numeric columns
        high_var = profile_data.get('key_variables', {}).get('high_variance', [])
        if high_var:
            features.append({
                'technique': 'binning',
                'priority': 'medium',
                'description': f'Create binned versions of {len(high_var)} high-variance columns',
                'columns': [c['column'] for c in high_var],
                'methods': ['equal_width', 'equal_frequency', 'kmeans'],
                'reason': 'Binning can capture non-linear patterns'
            })
        
        # Aggregation features from categories
        cat_cols = list(profile_data.get('categorical_profile', {}).keys())
        numeric_cols = list(profile_data.get('numeric_profile', {}).keys())
        
        if cat_cols and numeric_cols:
            features.append({
                'technique': 'aggregation_features',
                'priority': 'medium',
                'description': 'Create aggregated features by grouping categorical variables',
                'group_by': cat_cols[:3],  # Top 3 categorical
                'aggregate': numeric_cols[:3],  # Top 3 numeric
                'functions': ['mean', 'median', 'std', 'min', 'max'],
                'reason': 'Group-level statistics often predictive'
            })
        
        # Polynomial features (with caution)
        if 2 <= len(numeric_cols) <= 5:
            features.append({
                'technique': 'polynomial_features',
                'priority': 'low',
                'description': f'Create polynomial features (degree 2) from {len(numeric_cols)} numeric columns',
                'columns': numeric_cols,
                'degree': 2,
                'reason': 'Small number of features - polynomial expansion feasible',
                'warning': 'May cause overfitting - use with regularization'
            })
        
        return features
    
    def _recommend_modeling_approaches(
        self,
        profile_data: Dict[str, Any],
        data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Recommend machine learning modeling approaches"""
        modeling = []
        
        # Identify potential target variables
        targets = profile_data.get('key_variables', {}).get('potential_targets', [])
        
        if targets:
            for target in targets[:3]:  # Top 3 targets
                col = target['column']
                unique_vals = target['unique_values']
                
                if unique_vals == 2:
                    # Binary classification
                    modeling.append({
                        'task': 'binary_classification',
                        'priority': 'high',
                        'target': col,
                        'description': f'Predict {col} (binary outcome)',
                        'recommended_models': [
                            'Logistic Regression',
                            'Random Forest',
                            'XGBoost',
                            'LightGBM',
                            'Neural Network'
                        ],
                        'evaluation_metrics': ['accuracy', 'precision', 'recall', 'F1', 'AUC-ROC'],
                        'reason': 'Binary target detected'
                    })
                
                elif 3 <= unique_vals <= 10:
                    # Multi-class classification
                    modeling.append({
                        'task': 'multiclass_classification',
                        'priority': 'high',
                        'target': col,
                        'description': f'Predict {col} ({unique_vals} classes)',
                        'recommended_models': [
                            'Random Forest',
                            'XGBoost',
                            'LightGBM',
                            'Neural Network',
                            'SVM'
                        ],
                        'evaluation_metrics': ['accuracy', 'macro_F1', 'weighted_F1', 'confusion_matrix'],
                        'reason': f'{unique_vals}-class classification problem'
                    })
        
        # Regression for continuous numeric targets
        numeric_cols = list(profile_data.get('numeric_profile', {}).keys())
        if numeric_cols:
            # Recommend regression for first numeric column
            modeling.append({
                'task': 'regression',
                'priority': 'medium',
                'target': numeric_cols[0],
                'description': f'Predict {numeric_cols[0]} (continuous value)',
                'recommended_models': [
                    'Linear Regression',
                    'Ridge/Lasso',
                    'Random Forest Regressor',
                    'XGBoost Regressor',
                    'Neural Network'
                ],
                'evaluation_metrics': ['MAE', 'RMSE', 'R²', 'MAPE'],
                'reason': 'Continuous numeric variable available'
            })
        
        # Clustering for unsupervised learning
        if len(numeric_cols) >= 3:
            modeling.append({
                'task': 'clustering',
                'priority': 'low',
                'description': 'Discover natural groupings in the data',
                'recommended_models': [
                    'K-Means',
                    'DBSCAN',
                    'Hierarchical Clustering',
                    'Gaussian Mixture'
                ],
                'evaluation_metrics': ['silhouette_score', 'davies_bouldin_score'],
                'reason': 'Multiple numeric features - clustering applicable'
            })
        
        # Time series forecasting
        if profile_data.get('datetime_profile') and numeric_cols:
            modeling.append({
                'task': 'time_series_forecasting',
                'priority': 'high',
                'target': numeric_cols[0],
                'description': f'Forecast future values of {numeric_cols[0]}',
                'recommended_models': [
                    'ARIMA',
                    'SARIMA',
                    'Prophet',
                    'LSTM',
                    'XGBoost (with lag features)'
                ],
                'evaluation_metrics': ['MAE', 'RMSE', 'MAPE'],
                'reason': 'Temporal data present - forecasting applicable'
            })
        
        # Anomaly detection if outliers present
        outliers = profile_data.get('outliers', {})
        if any(stats.get('has_outliers', False) for stats in outliers.values()):
            modeling.append({
                'task': 'anomaly_detection',
                'priority': 'medium',
                'description': 'Identify unusual patterns or anomalies',
                'recommended_models': [
                    'Isolation Forest',
                    'Local Outlier Factor',
                    'One-Class SVM',
                    'Autoencoder'
                ],
                'evaluation_metrics': ['precision', 'recall', 'F1'],
                'reason': 'Outliers detected - anomaly detection relevant'
            })
        
        return modeling
    
    def _recommend_data_quality_improvements(
        self,
        profile_data: Dict[str, Any],
        data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Recommend data quality improvements"""
        return profile_data.get('data_quality', {}).get('recommendations', [])
    
    def _recommend_next_steps(
        self,
        profile_data: Dict[str, Any],
        insights: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Recommend prioritized next steps"""
        steps = []
        
        # Step 1: Always start with data quality
        quality_score = profile_data.get('data_quality', {}).get('overall_quality_score', 0)
        if quality_score < 80:
            steps.append({
                'step': '1. Address data quality issues',
                'description': f'Current quality score: {quality_score:.1f}/100. Clean missing values, duplicates, and outliers.',
                'priority': 'critical'
            })
        
        # Step 2: Exploratory visualization
        steps.append({
            'step': '2. Create exploratory visualizations',
            'description': 'Generate correlation heatmaps, distributions, and scatter plots to understand patterns.',
            'priority': 'high'
        })
        
        # Step 3: Feature engineering
        steps.append({
            'step': '3. Engineer new features',
            'description': 'Extract datetime features, create interactions, and aggregate by categories.',
            'priority': 'high'
        })
        
        # Step 4: Statistical analysis
        strong_corrs = profile_data.get('correlations', {}).get('num_strong_correlations', 0)
        if strong_corrs > 0:
            steps.append({
                'step': '4. Investigate correlations',
                'description': f'{strong_corrs} strong correlations found. Perform deeper statistical analysis.',
                'priority': 'medium'
            })
        
        # Step 5: Modeling
        targets = profile_data.get('key_variables', {}).get('potential_targets', [])
        if targets:
            steps.append({
                'step': '5. Build predictive models',
                'description': f'Try classification/regression using {targets[0]["column"]} as target.',
                'priority': 'medium'
            })
        
        # Step 6: Deployment
        steps.append({
            'step': '6. Deploy and monitor',
            'description': 'Once models are validated, deploy to production and set up monitoring.',
            'priority': 'low'
        })
        
        return steps
