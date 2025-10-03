"""
Performance Optimizer
Optimize dashboard generation for large datasets
"""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from functools import lru_cache
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """
    Optimize dashboard generation performance for large datasets
    Includes data sampling, caching, and lazy loading strategies
    """
    
    def __init__(
        self,
        cache_size: int = 128,
        sample_threshold: int = 10000,
        max_sample_size: int = 5000
    ):
        """
        Initialize optimizer
        
        Args:
            cache_size: LRU cache size for computed results
            sample_threshold: Row count threshold for automatic sampling
            max_sample_size: Maximum rows in sampled dataset
        """
        self.cache_size = cache_size
        self.sample_threshold = sample_threshold
        self.max_sample_size = max_sample_size
        self.performance_metrics = []
    
    def should_sample(self, data: pd.DataFrame) -> bool:
        """
        Determine if data should be sampled
        
        Args:
            data: Input dataframe
            
        Returns:
            True if data exceeds sampling threshold
        """
        return len(data) > self.sample_threshold
    
    def smart_sample(
        self,
        data: pd.DataFrame,
        method: str = "auto",
        preserve_distributions: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Intelligently sample large datasets while preserving statistical properties
        
        Args:
            data: Input dataframe
            method: Sampling method ('auto', 'random', 'stratified', 'systematic')
            preserve_distributions: Whether to preserve category distributions
            
        Returns:
            Tuple of (sampled_data, sampling_info)
        """
        start_time = datetime.now()
        original_size = len(data)
        
        if not self.should_sample(data):
            return data, {
                "sampled": False,
                "original_size": original_size,
                "sample_size": original_size,
                "method": "none"
            }
        
        try:
            # Auto-select sampling method
            if method == "auto":
                # Use stratified if categorical columns exist
                categorical_cols = data.select_dtypes(include=['object', 'category']).columns
                method = "stratified" if len(categorical_cols) > 0 else "random"
            
            sample_size = min(self.max_sample_size, original_size)
            
            if method == "random":
                sampled_data = self._random_sample(data, sample_size)
            elif method == "stratified":
                sampled_data = self._stratified_sample(data, sample_size, preserve_distributions)
            elif method == "systematic":
                sampled_data = self._systematic_sample(data, sample_size)
            else:
                raise ValueError(f"Unknown sampling method: {method}")
            
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            sampling_info = {
                "sampled": True,
                "original_size": original_size,
                "sample_size": len(sampled_data),
                "reduction_ratio": len(sampled_data) / original_size,
                "method": method,
                "elapsed_ms": round(elapsed_ms, 2)
            }
            
            logger.info(f"Sampled {original_size} rows → {len(sampled_data)} rows using {method} method")
            
            return sampled_data, sampling_info
            
        except Exception as e:
            logger.error(f"Error during sampling: {str(e)}")
            # Fallback to simple random sample
            sampled_data = data.sample(n=min(self.max_sample_size, len(data)), random_state=42)
            return sampled_data, {
                "sampled": True,
                "original_size": original_size,
                "sample_size": len(sampled_data),
                "method": "fallback_random",
                "error": str(e)
            }
    
    def _random_sample(self, data: pd.DataFrame, sample_size: int) -> pd.DataFrame:
        """Random sampling"""
        return data.sample(n=sample_size, random_state=42)
    
    def _stratified_sample(
        self,
        data: pd.DataFrame,
        sample_size: int,
        preserve_distributions: bool
    ) -> pd.DataFrame:
        """
        Stratified sampling to preserve category distributions
        """
        # Find best stratification column (categorical with reasonable cardinality)
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns
        
        stratify_col = None
        for col in categorical_cols:
            unique_count = data[col].nunique()
            if 2 <= unique_count <= 50:  # Reasonable number of categories
                stratify_col = col
                break
        
        if stratify_col is None:
            # Fallback to random if no suitable column
            return self._random_sample(data, sample_size)
        
        # Calculate samples per stratum
        value_counts = data[stratify_col].value_counts()
        samples_per_category = {}
        
        for category, count in value_counts.items():
            proportion = count / len(data)
            samples_per_category[category] = max(1, int(sample_size * proportion))
        
        # Adjust to match exact sample_size
        total_samples = sum(samples_per_category.values())
        if total_samples > sample_size:
            # Reduce largest categories
            diff = total_samples - sample_size
            sorted_cats = sorted(samples_per_category.items(), key=lambda x: x[1], reverse=True)
            for cat, _ in sorted_cats[:diff]:
                samples_per_category[cat] -= 1
        
        # Sample from each stratum
        sampled_dfs = []
        for category, n_samples in samples_per_category.items():
            category_data = data[data[stratify_col] == category]
            if len(category_data) > 0:
                n = min(n_samples, len(category_data))
                sampled_dfs.append(category_data.sample(n=n, random_state=42))
        
        return pd.concat(sampled_dfs, ignore_index=True)
    
    def _systematic_sample(self, data: pd.DataFrame, sample_size: int) -> pd.DataFrame:
        """
        Systematic sampling - select every k-th row
        """
        k = len(data) // sample_size
        indices = np.arange(0, len(data), k)[:sample_size]
        return data.iloc[indices].copy()
    
    def get_data_hash(self, data: pd.DataFrame) -> str:
        """
        Generate hash for dataframe to use as cache key
        
        Args:
            data: Input dataframe
            
        Returns:
            MD5 hash string
        """
        # Use shape, column names, and sample values for hash
        hash_input = f"{data.shape}_{list(data.columns)}_{data.head(10).to_json()}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    @lru_cache(maxsize=128)
    def _cached_computation(self, data_hash: str, computation_type: str) -> Any:
        """
        Cache expensive computations (decorator pattern)
        This is a placeholder - actual implementations would cache specific computations
        """
        logger.info(f"Cache miss for {computation_type} with hash {data_hash[:8]}...")
        return None
    
    def optimize_chart_generation(
        self,
        data: pd.DataFrame,
        chart_type: str,
        **chart_params
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Optimize data before chart generation
        
        Args:
            data: Input dataframe
            chart_type: Type of chart to generate
            **chart_params: Chart-specific parameters
            
        Returns:
            Tuple of (optimized_data, optimization_info)
        """
        start_time = datetime.now()
        optimization_info = {
            "chart_type": chart_type,
            "original_rows": len(data),
            "optimizations_applied": []
        }
        
        optimized_data = data
        
        # Apply sampling if needed
        if self.should_sample(data):
            # Choose sampling method based on chart type
            if chart_type in ['histogram', 'box_plot', 'violin_plot']:
                method = "random"  # Distribution-based charts
            elif chart_type in ['bar', 'pie', 'treemap']:
                method = "stratified"  # Category-based charts
            else:
                method = "auto"
            
            optimized_data, sampling_info = self.smart_sample(data, method=method)
            optimization_info["optimizations_applied"].append("sampling")
            optimization_info["sampling"] = sampling_info
        
        # Chart-specific optimizations
        if chart_type == "scatter":
            # Limit scatter plot points for performance
            if len(optimized_data) > 1000:
                optimized_data = optimized_data.sample(n=1000, random_state=42)
                optimization_info["optimizations_applied"].append("scatter_point_limit")
        
        elif chart_type in ["line", "area", "stacked_area"]:
            # Aggregate time series data if too granular
            time_col = chart_params.get('time_column')
            if time_col and len(optimized_data) > 500:
                optimized_data = self._aggregate_timeseries(optimized_data, time_col)
                optimization_info["optimizations_applied"].append("timeseries_aggregation")
        
        elif chart_type == "sankey":
            # Limit number of nodes/links for Sankey diagrams
            if len(optimized_data) > 200:
                optimized_data = optimized_data.head(200)
                optimization_info["optimizations_applied"].append("sankey_link_limit")
        
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        optimization_info["elapsed_ms"] = round(elapsed_ms, 2)
        optimization_info["final_rows"] = len(optimized_data)
        optimization_info["reduction_ratio"] = len(optimized_data) / len(data) if len(data) > 0 else 1.0
        
        return optimized_data, optimization_info
    
    def _aggregate_timeseries(
        self,
        data: pd.DataFrame,
        time_column: str
    ) -> pd.DataFrame:
        """
        Aggregate time series data to reduce granularity
        """
        try:
            # Convert to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(data[time_column]):
                data[time_column] = pd.to_datetime(data[time_column])
            
            # Determine appropriate frequency based on data range
            time_range = (data[time_column].max() - data[time_column].min()).days
            
            if time_range > 365:
                freq = 'W'  # Weekly
            elif time_range > 90:
                freq = 'D'  # Daily
            else:
                freq = 'H'  # Hourly
            
            # Group and aggregate
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            aggregated = data.groupby(pd.Grouper(key=time_column, freq=freq))[numeric_cols].mean().reset_index()
            
            return aggregated
            
        except Exception as e:
            logger.warning(f"Timeseries aggregation failed: {str(e)}")
            return data
    
    def get_performance_recommendations(
        self,
        data: pd.DataFrame
    ) -> List[Dict[str, str]]:
        """
        Analyze data and provide performance recommendations
        
        Args:
            data: Input dataframe
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Check dataset size
        if len(data) > 50000:
            recommendations.append({
                "category": "Data Size",
                "severity": "high",
                "message": f"Dataset has {len(data):,} rows. Consider enabling automatic sampling.",
                "action": "Enable smart_sample() with preserve_distributions=True"
            })
        elif len(data) > 10000:
            recommendations.append({
                "category": "Data Size",
                "severity": "medium",
                "message": f"Dataset has {len(data):,} rows. May benefit from sampling.",
                "action": "Consider using smart_sample() for faster visualization"
            })
        
        # Check column count
        if len(data.columns) > 50:
            recommendations.append({
                "category": "Dimensionality",
                "severity": "medium",
                "message": f"Dataset has {len(data.columns)} columns. Too many for effective visualization.",
                "action": "Select key columns for dashboard or use dimensionality reduction"
            })
        
        # Check for high cardinality categorical columns
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            unique_count = data[col].nunique()
            if unique_count > 100:
                recommendations.append({
                    "category": "Cardinality",
                    "severity": "low",
                    "message": f"Column '{col}' has {unique_count} unique values.",
                    "action": f"Consider grouping rare categories or filtering top N values"
                })
        
        # Check memory usage
        memory_mb = data.memory_usage(deep=True).sum() / (1024 * 1024)
        if memory_mb > 100:
            recommendations.append({
                "category": "Memory",
                "severity": "high",
                "message": f"Dataset uses {memory_mb:.1f} MB of memory.",
                "action": "Use data sampling or convert object columns to categories"
            })
        
        # Check for missing values
        missing_pct = (data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100
        if missing_pct > 10:
            recommendations.append({
                "category": "Data Quality",
                "severity": "medium",
                "message": f"{missing_pct:.1f}% of data is missing.",
                "action": "Clean data before visualization for better insights"
            })
        
        return recommendations
    
    def track_performance(
        self,
        operation: str,
        elapsed_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track performance metrics for operations
        
        Args:
            operation: Name of operation
            elapsed_ms: Time elapsed in milliseconds
            metadata: Additional metadata
        """
        metric = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "elapsed_ms": elapsed_ms,
            "metadata": metadata or {}
        }
        self.performance_metrics.append(metric)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get summary of tracked performance metrics
        
        Returns:
            Dictionary with performance statistics
        """
        if not self.performance_metrics:
            return {"total_operations": 0}
        
        operations = [m['operation'] for m in self.performance_metrics]
        elapsed_times = [m['elapsed_ms'] for m in self.performance_metrics]
        
        return {
            "total_operations": len(self.performance_metrics),
            "total_time_ms": sum(elapsed_times),
            "avg_time_ms": np.mean(elapsed_times),
            "max_time_ms": max(elapsed_times),
            "operations_breakdown": {
                op: {
                    "count": operations.count(op),
                    "avg_time_ms": np.mean([m['elapsed_ms'] for m in self.performance_metrics if m['operation'] == op])
                }
                for op in set(operations)
            }
        }
    
    def reset_metrics(self):
        """Reset performance tracking"""
        self.performance_metrics = []
