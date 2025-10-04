"""
Data Profiler Module
Performs comprehensive data profiling and pattern discovery including:
- Correlation analysis (Pearson, Spearman)
- High-cardinality feature detection
- Outlier detection (z-score, IQR)
- Key variable identification
- Statistical summaries
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional
import warnings

warnings.filterwarnings('ignore')


class DataProfiler:
    """
    Analyzes datasets to extract statistical profiles, correlations,
    outliers, and patterns for insight generation.
    """
    
    def __init__(self):
        """Initialize the DataProfiler"""
        self.profile_data = {}
        self.correlation_threshold = 0.7
        self.outlier_threshold_zscore = 3
        self.high_cardinality_threshold = 50
        
    def profile_dataset(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive profiling of the entire dataset.
        
        Args:
            data: Input DataFrame
            
        Returns:
            Dictionary containing complete dataset profile
        """
        profile = {
            'basic_info': self._get_basic_info(data),
            'numeric_profile': self._profile_numeric_columns(data),
            'categorical_profile': self._profile_categorical_columns(data),
            'datetime_profile': self._profile_datetime_columns(data),
            'correlations': self._analyze_correlations(data),
            'outliers': self._detect_outliers(data),
            'missing_patterns': self._analyze_missing_data(data),
            'key_variables': self._identify_key_variables(data),
            'data_quality': self._assess_data_quality(data)
        }
        
        self.profile_data = profile
        return profile
    
    def _get_basic_info(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extract basic dataset information"""
        return {
            'num_rows': len(data),
            'num_columns': len(data.columns),
            'memory_usage_mb': data.memory_usage(deep=True).sum() / (1024 * 1024),
            'duplicate_rows': data.duplicated().sum(),
            'total_missing_values': data.isnull().sum().sum(),
            'missing_percentage': (data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100,
            'column_types': data.dtypes.value_counts().to_dict()
        }
    
    def _profile_numeric_columns(self, data: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Profile all numeric columns"""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        profiles = {}
        
        for col in numeric_cols:
            col_data = data[col].dropna()
            
            if len(col_data) == 0:
                continue
                
            profiles[col] = {
                'count': len(col_data),
                'missing': data[col].isnull().sum(),
                'missing_pct': (data[col].isnull().sum() / len(data)) * 100,
                'mean': float(col_data.mean()),
                'median': float(col_data.median()),
                'std': float(col_data.std()),
                'min': float(col_data.min()),
                'max': float(col_data.max()),
                'q1': float(col_data.quantile(0.25)),
                'q3': float(col_data.quantile(0.75)),
                'iqr': float(col_data.quantile(0.75) - col_data.quantile(0.25)),
                'variance': float(col_data.var()),
                'skewness': float(col_data.skew()),
                'kurtosis': float(col_data.kurtosis()),
                'coefficient_of_variation': float((col_data.std() / col_data.mean()) * 100) if col_data.mean() != 0 else 0,
                'unique_values': int(col_data.nunique()),
                'zeros_count': int((col_data == 0).sum()),
                'zeros_pct': float(((col_data == 0).sum() / len(col_data)) * 100),
                'range': float(col_data.max() - col_data.min()),
                'is_binary': bool(col_data.nunique() == 2),
                'is_constant': bool(col_data.nunique() == 1)
            }
            
        return profiles
    
    def _profile_categorical_columns(self, data: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Profile all categorical columns"""
        cat_cols = data.select_dtypes(include=['object', 'category']).columns
        profiles = {}
        
        for col in cat_cols:
            col_data = data[col].dropna()
            
            if len(col_data) == 0:
                continue
                
            value_counts = col_data.value_counts()
            
            profiles[col] = {
                'count': len(col_data),
                'missing': data[col].isnull().sum(),
                'missing_pct': (data[col].isnull().sum() / len(data)) * 100,
                'unique_values': int(col_data.nunique()),
                'cardinality': 'high' if col_data.nunique() > self.high_cardinality_threshold else 'low',
                'most_common': value_counts.index[0] if len(value_counts) > 0 else None,
                'most_common_freq': int(value_counts.values[0]) if len(value_counts) > 0 else 0,
                'most_common_pct': float((value_counts.values[0] / len(col_data)) * 100) if len(value_counts) > 0 else 0,
                'least_common': value_counts.index[-1] if len(value_counts) > 0 else None,
                'least_common_freq': int(value_counts.values[-1]) if len(value_counts) > 0 else 0,
                'top_5_values': value_counts.head(5).to_dict(),
                'entropy': float(stats.entropy(value_counts)),
                'is_constant': bool(col_data.nunique() == 1),
                'is_binary': bool(col_data.nunique() == 2)
            }
            
        return profiles
    
    def _profile_datetime_columns(self, data: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Profile datetime columns"""
        datetime_cols = data.select_dtypes(include=['datetime64']).columns
        profiles = {}
        
        for col in datetime_cols:
            col_data = data[col].dropna()
            
            if len(col_data) == 0:
                continue
                
            profiles[col] = {
                'count': len(col_data),
                'missing': data[col].isnull().sum(),
                'missing_pct': (data[col].isnull().sum() / len(data)) * 100,
                'min_date': str(col_data.min()),
                'max_date': str(col_data.max()),
                'date_range_days': (col_data.max() - col_data.min()).days,
                'unique_dates': int(col_data.nunique()),
                'most_common_date': str(col_data.mode()[0]) if len(col_data.mode()) > 0 else None,
                'year_range': list(col_data.dt.year.unique()),
                'month_distribution': col_data.dt.month.value_counts().to_dict(),
                'day_of_week_distribution': col_data.dt.dayofweek.value_counts().to_dict(),
                'has_time_component': bool((col_data.dt.hour != 0).any() or (col_data.dt.minute != 0).any())
            }
            
        return profiles
    
    def _analyze_correlations(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze correlations between numeric variables.
        Returns both Pearson and Spearman correlations.
        """
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.shape[1] < 2:
            return {
                'pearson_matrix': {},
                'spearman_matrix': {},
                'strong_correlations': [],
                'correlation_pairs': []
            }
        
        # Calculate correlation matrices
        pearson_corr = numeric_data.corr(method='pearson')
        spearman_corr = numeric_data.corr(method='spearman')
        
        # Find strong correlations
        strong_correlations = []
        correlation_pairs = []
        
        for i in range(len(pearson_corr.columns)):
            for j in range(i + 1, len(pearson_corr.columns)):
                col1 = pearson_corr.columns[i]
                col2 = pearson_corr.columns[j]
                pearson_val = pearson_corr.iloc[i, j]
                spearman_val = spearman_corr.iloc[i, j]
                
                if abs(pearson_val) > self.correlation_threshold or abs(spearman_val) > self.correlation_threshold:
                    strong_correlations.append({
                        'variable_1': col1,
                        'variable_2': col2,
                        'pearson': float(pearson_val),
                        'spearman': float(spearman_val),
                        'strength': 'strong' if abs(pearson_val) > 0.8 else 'moderate',
                        'direction': 'positive' if pearson_val > 0 else 'negative'
                    })
                
                correlation_pairs.append({
                    'variable_1': col1,
                    'variable_2': col2,
                    'pearson': float(pearson_val),
                    'spearman': float(spearman_val)
                })
        
        return {
            'pearson_matrix': pearson_corr.to_dict(),
            'spearman_matrix': spearman_corr.to_dict(),
            'strong_correlations': strong_correlations,
            'correlation_pairs': correlation_pairs[:50],  # Limit to top 50
            'num_strong_correlations': len(strong_correlations)
        }
    
    def _detect_outliers(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect outliers using both z-score and IQR methods.
        """
        numeric_data = data.select_dtypes(include=[np.number])
        outlier_report = {}
        
        for col in numeric_data.columns:
            col_data = data[col].dropna()
            
            if len(col_data) == 0:
                continue
            
            # Z-score method
            z_scores = np.abs(stats.zscore(col_data))
            z_outliers = np.where(z_scores > self.outlier_threshold_zscore)[0]
            
            # IQR method
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            iqr_outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
            
            outlier_report[col] = {
                'z_score_outliers': int(len(z_outliers)),
                'z_score_outlier_pct': float((len(z_outliers) / len(col_data)) * 100),
                'iqr_outliers': int(len(iqr_outliers)),
                'iqr_outlier_pct': float((len(iqr_outliers) / len(col_data)) * 100),
                'iqr_lower_bound': float(lower_bound),
                'iqr_upper_bound': float(upper_bound),
                'outlier_values_sample': col_data[z_scores > self.outlier_threshold_zscore].head(10).tolist(),
                'has_outliers': bool(len(z_outliers) > 0 or len(iqr_outliers) > 0)
            }
        
        return outlier_report
    
    def _analyze_missing_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in missing data"""
        missing_counts = data.isnull().sum()
        missing_pct = (missing_counts / len(data)) * 100
        
        columns_with_missing = missing_counts[missing_counts > 0].to_dict()
        
        return {
            'total_missing': int(data.isnull().sum().sum()),
            'columns_with_missing': columns_with_missing,
            'columns_with_missing_pct': {k: float(missing_pct[k]) for k in columns_with_missing.keys()},
            'complete_rows': int(data.dropna().shape[0]),
            'complete_rows_pct': float((data.dropna().shape[0] / len(data)) * 100),
            'rows_with_any_missing': int(data.isnull().any(axis=1).sum()),
            'rows_with_any_missing_pct': float((data.isnull().any(axis=1).sum() / len(data)) * 100)
        }
    
    def _identify_key_variables(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Identify potentially important variables based on:
        - High variance
        - Strong correlations
        - Low missing data
        - Unique identifiers
        """
        numeric_data = data.select_dtypes(include=[np.number])
        
        key_vars = {
            'high_variance': [],
            'low_variance': [],
            'potential_ids': [],
            'potential_targets': [],
            'complete_columns': []
        }
        
        if len(numeric_data.columns) > 0:
            # High variance columns (normalized by mean)
            for col in numeric_data.columns:
                col_data = data[col].dropna()
                if len(col_data) > 0 and col_data.mean() != 0:
                    cv = (col_data.std() / col_data.mean()) * 100
                    if cv > 50:  # High coefficient of variation
                        key_vars['high_variance'].append({
                            'column': col,
                            'coefficient_of_variation': float(cv)
                        })
                    elif cv < 10:  # Low coefficient of variation
                        key_vars['low_variance'].append({
                            'column': col,
                            'coefficient_of_variation': float(cv)
                        })
            
            # Potential ID columns (unique values == num rows)
            for col in data.columns:
                if data[col].nunique() == len(data):
                    key_vars['potential_ids'].append(col)
        
        # Complete columns (no missing values)
        for col in data.columns:
            if data[col].isnull().sum() == 0:
                key_vars['complete_columns'].append(col)
        
        # Potential target variables (binary or low cardinality categorical)
        for col in data.columns:
            unique_count = data[col].nunique()
            if 2 <= unique_count <= 10:
                key_vars['potential_targets'].append({
                    'column': col,
                    'unique_values': int(unique_count),
                    'type': str(data[col].dtype)
                })
        
        return key_vars
    
    def _assess_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Assess overall data quality with a scoring system.
        """
        total_cells = len(data) * len(data.columns)
        missing_cells = data.isnull().sum().sum()
        
        # Quality metrics
        completeness_score = ((total_cells - missing_cells) / total_cells) * 100
        uniqueness_score = (data.drop_duplicates().shape[0] / len(data)) * 100
        
        # Consistency score (columns with expected data types)
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        consistency_score = 100.0  # Default high score
        
        # Overall quality score
        overall_score = (completeness_score * 0.4 + uniqueness_score * 0.3 + consistency_score * 0.3)
        
        return {
            'completeness_score': float(completeness_score),
            'uniqueness_score': float(uniqueness_score),
            'consistency_score': float(consistency_score),
            'overall_quality_score': float(overall_score),
            'quality_grade': self._get_quality_grade(overall_score),
            'recommendations': self._get_quality_recommendations(data)
        }
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade"""
        if score >= 90:
            return 'A - Excellent'
        elif score >= 80:
            return 'B - Good'
        elif score >= 70:
            return 'C - Fair'
        elif score >= 60:
            return 'D - Poor'
        else:
            return 'F - Very Poor'
    
    def _get_quality_recommendations(self, data: pd.DataFrame) -> List[str]:
        """Generate data quality recommendations"""
        recommendations = []
        
        # Check for missing data
        missing_pct = (data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100
        if missing_pct > 10:
            recommendations.append(f"High missing data ({missing_pct:.1f}%) - Consider imputation or removal")
        
        # Check for duplicates
        dup_count = data.duplicated().sum()
        if dup_count > 0:
            recommendations.append(f"Found {dup_count} duplicate rows - Consider deduplication")
        
        # Check for constant columns
        for col in data.columns:
            if data[col].nunique() == 1:
                recommendations.append(f"Column '{col}' has constant value - Consider removing")
        
        # Check for high cardinality
        for col in data.select_dtypes(include=['object']).columns:
            if data[col].nunique() > self.high_cardinality_threshold:
                recommendations.append(f"Column '{col}' has high cardinality ({data[col].nunique()} unique values) - May need encoding")
        
        if not recommendations:
            recommendations.append("Data quality looks good - No major issues detected")
        
        return recommendations
    
    def get_summary(self) -> str:
        """Get a text summary of the profiling results"""
        if not self.profile_data:
            return "No profiling data available. Run profile_dataset() first."
        
        basic = self.profile_data['basic_info']
        quality = self.profile_data['data_quality']
        
        summary = f"""
Dataset Profile Summary
=======================
Rows: {basic['num_rows']:,}
Columns: {basic['num_columns']}
Memory: {basic['memory_usage_mb']:.2f} MB
Duplicates: {basic['duplicate_rows']}
Missing Values: {basic['total_missing_values']:,} ({basic['missing_percentage']:.2f}%)

Quality Score: {quality['overall_quality_score']:.1f}/100 ({quality['quality_grade']})

Strong Correlations: {self.profile_data['correlations']['num_strong_correlations']}
Key Variables Identified: {len(self.profile_data['key_variables']['potential_targets'])} potential targets
"""
        return summary.strip()
