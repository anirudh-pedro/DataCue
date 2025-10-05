"""
Cluster Evaluator
Evaluates clustering models using various metrics and visualization techniques.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.metrics import (
    silhouette_score, silhouette_samples,
    davies_bouldin_score, calinski_harabasz_score,
    adjusted_rand_score, adjusted_mutual_info_score
)
import logging

logger = logging.getLogger(__name__)


class ClusterEvaluator:
    """
    Evaluates clustering algorithms using multiple metrics.
    
    Metrics:
    - Silhouette Score (higher is better, range: -1 to 1)
    - Davies-Bouldin Index (lower is better)
    - Calinski-Harabasz Index (higher is better)
    - Inertia (for KMeans, lower is better)
    """
    
    def __init__(self):
        """Initialize cluster evaluator"""
        pass
    
    def evaluate_clustering(
        self,
        model,
        X: np.ndarray,
        labels: Optional[np.ndarray] = None,
        model_name: str = 'clustering_model'
    ) -> Dict[str, Any]:
        """
        Evaluate a clustering model.
        
        Args:
            model: Fitted clustering model
            X: Feature matrix
            labels: Cluster labels (if not from model)
            model_name: Name of the clustering algorithm
            
        Returns:
            Dictionary with clustering metrics
        """
        # Get cluster labels
        if labels is None:
            if hasattr(model, 'labels_'):
                labels = model.labels_
            elif hasattr(model, 'predict'):
                labels = model.predict(X)
            else:
                raise ValueError("Model has no labels_ attribute and cannot predict")
        
        # Filter out noise points (label -1 in DBSCAN)
        valid_mask = labels != -1
        X_valid = X[valid_mask]
        labels_valid = labels[valid_mask]
        
        n_clusters = len(np.unique(labels_valid))
        n_noise = np.sum(labels == -1)
        
        logger.info(f"   Evaluating {model_name}: {n_clusters} clusters, {n_noise} noise points")
        
        metrics = {
            'n_clusters': int(n_clusters),
            'n_noise_points': int(n_noise),
            'cluster_sizes': self._get_cluster_sizes(labels),
        }
        
        # Only compute metrics if we have valid clusters
        if n_clusters > 1 and len(X_valid) > n_clusters:
            # Silhouette Score
            try:
                silhouette = silhouette_score(X_valid, labels_valid)
                metrics['silhouette_score'] = float(silhouette)
                
                # Per-cluster silhouette scores
                silhouette_values = silhouette_samples(X_valid, labels_valid)
                metrics['silhouette_per_cluster'] = self._silhouette_per_cluster(
                    silhouette_values, labels_valid
                )
            except Exception as e:
                logger.warning(f"Could not compute silhouette score: {str(e)}")
                metrics['silhouette_score'] = None
            
            # Davies-Bouldin Index (lower is better)
            try:
                db_index = davies_bouldin_score(X_valid, labels_valid)
                metrics['davies_bouldin_index'] = float(db_index)
            except Exception as e:
                logger.warning(f"Could not compute Davies-Bouldin index: {str(e)}")
                metrics['davies_bouldin_index'] = None
            
            # Calinski-Harabasz Index (higher is better)
            try:
                ch_index = calinski_harabasz_score(X_valid, labels_valid)
                metrics['calinski_harabasz_index'] = float(ch_index)
            except Exception as e:
                logger.warning(f"Could not compute Calinski-Harabasz index: {str(e)}")
                metrics['calinski_harabasz_index'] = None
        else:
            logger.warning(f"Not enough clusters or samples for metric computation")
            metrics['silhouette_score'] = None
            metrics['davies_bouldin_index'] = None
            metrics['calinski_harabasz_index'] = None
        
        # Inertia (for KMeans)
        if hasattr(model, 'inertia_'):
            metrics['inertia'] = float(model.inertia_)
        
        # Cluster centers (for centroid-based methods)
        if hasattr(model, 'cluster_centers_'):
            metrics['cluster_centers'] = model.cluster_centers_.tolist()
        
        return metrics
    
    def evaluate_multiple_k(
        self,
        model_class,
        X: np.ndarray,
        k_range: range,
        model_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Evaluate clustering for multiple values of k (n_clusters).
        Useful for finding optimal number of clusters.
        
        Args:
            model_class: Clustering model class
            X: Feature matrix
            k_range: Range of k values to try
            model_params: Additional model parameters
            
        Returns:
            Dictionary with metrics for each k
        """
        if model_params is None:
            model_params = {}
        
        results = []
        
        for k in k_range:
            try:
                # Create and fit model
                params = {**model_params, 'n_clusters': k}
                if 'n_components' in model_class.__init__.__code__.co_varnames:
                    params['n_components'] = params.pop('n_clusters')
                
                model = model_class(**params)
                model.fit(X)
                
                # Evaluate
                metrics = self.evaluate_clustering(model, X, model_name=f'k={k}')
                metrics['k'] = k
                results.append(metrics)
                
            except Exception as e:
                logger.warning(f"Failed to evaluate k={k}: {str(e)}")
        
        # Find optimal k
        optimal_k = self._find_optimal_k(results)
        
        return {
            'results_per_k': results,
            'optimal_k': optimal_k,
            'recommendation': self._get_k_recommendation(results, optimal_k)
        }
    
    def elbow_analysis(
        self,
        X: np.ndarray,
        k_range: range,
        model_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Perform elbow method analysis for KMeans.
        
        Args:
            X: Feature matrix
            k_range: Range of k values
            model_params: Additional parameters
            
        Returns:
            Dictionary with inertia values and elbow point
        """
        from sklearn.cluster import KMeans
        
        if model_params is None:
            model_params = {}
        
        inertias = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, **model_params)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)
        
        # Find elbow point using rate of change
        elbow_k = self._find_elbow_point(list(k_range), inertias)
        
        return {
            'k_values': list(k_range),
            'inertias': inertias,
            'elbow_k': elbow_k,
            'recommendation': f"Elbow method suggests k={elbow_k}"
        }
    
    def compare_clustering_algorithms(
        self,
        models: Dict[str, Any],
        X: np.ndarray
    ) -> pd.DataFrame:
        """
        Compare multiple clustering algorithms.
        
        Args:
            models: Dictionary of {name: fitted_model}
            X: Feature matrix
            
        Returns:
            Comparison DataFrame
        """
        results = []
        
        for name, model in models.items():
            metrics = self.evaluate_clustering(model, X, model_name=name)
            results.append({
                'algorithm': name,
                'n_clusters': metrics.get('n_clusters'),
                'silhouette': metrics.get('silhouette_score'),
                'davies_bouldin': metrics.get('davies_bouldin_index'),
                'calinski_harabasz': metrics.get('calinski_harabasz_index'),
                'n_noise': metrics.get('n_noise_points', 0)
            })
        
        df = pd.DataFrame(results)
        
        # Rank algorithms
        df['rank'] = self._rank_clustering_algorithms(df)
        df = df.sort_values('rank')
        
        return df
    
    def _get_cluster_sizes(self, labels: np.ndarray) -> Dict[int, int]:
        """Get size of each cluster"""
        unique, counts = np.unique(labels, return_counts=True)
        return {int(label): int(count) for label, count in zip(unique, counts)}
    
    def _silhouette_per_cluster(
        self,
        silhouette_values: np.ndarray,
        labels: np.ndarray
    ) -> Dict[int, float]:
        """Calculate average silhouette score per cluster"""
        per_cluster = {}
        for label in np.unique(labels):
            mask = labels == label
            per_cluster[int(label)] = float(np.mean(silhouette_values[mask]))
        return per_cluster
    
    def _find_optimal_k(self, results: List[Dict]) -> int:
        """
        Find optimal k based on multiple criteria.
        Uses silhouette score as primary metric.
        """
        valid_results = [r for r in results if r.get('silhouette_score') is not None]
        
        if not valid_results:
            return results[0]['k'] if results else 2
        
        # Find k with highest silhouette score
        best = max(valid_results, key=lambda x: x['silhouette_score'])
        return best['k']
    
    def _get_k_recommendation(
        self,
        results: List[Dict],
        optimal_k: int
    ) -> str:
        """Generate recommendation for k selection"""
        optimal_result = next((r for r in results if r['k'] == optimal_k), None)
        
        if not optimal_result:
            return f"Recommended k={optimal_k}"
        
        silhouette = optimal_result.get('silhouette_score')
        
        if silhouette is None:
            return f"Recommended k={optimal_k} (metrics unavailable)"
        elif silhouette > 0.7:
            return f"Strong clustering structure found with k={optimal_k} (silhouette={silhouette:.3f})"
        elif silhouette > 0.5:
            return f"Reasonable clustering with k={optimal_k} (silhouette={silhouette:.3f})"
        elif silhouette > 0.25:
            return f"Weak clustering structure with k={optimal_k} (silhouette={silhouette:.3f})"
        else:
            return f"Poor clustering structure with k={optimal_k} (silhouette={silhouette:.3f}). Consider different algorithm."
    
    def _find_elbow_point(self, k_values: List[int], inertias: List[float]) -> int:
        """
        Find elbow point using maximum curvature method.
        """
        if len(k_values) < 3:
            return k_values[0]
        
        # Calculate rate of change
        rates = []
        for i in range(1, len(inertias)):
            rate = inertias[i-1] - inertias[i]
            rates.append(rate)
        
        # Find point where rate change decreases most
        if len(rates) < 2:
            return k_values[1]
        
        rate_changes = []
        for i in range(1, len(rates)):
            change = rates[i-1] - rates[i]
            rate_changes.append(change)
        
        # Elbow is where rate change is maximum
        elbow_idx = rate_changes.index(max(rate_changes)) + 2
        return k_values[elbow_idx] if elbow_idx < len(k_values) else k_values[-1]
    
    def _rank_clustering_algorithms(self, df: pd.DataFrame) -> List[int]:
        """
        Rank clustering algorithms based on metrics.
        Lower rank number is better.
        """
        ranks = []
        
        for idx, row in df.iterrows():
            score = 0
            
            # Silhouette (higher is better)
            if pd.notna(row['silhouette']):
                score += row['silhouette'] * 100
            
            # Davies-Bouldin (lower is better)
            if pd.notna(row['davies_bouldin']):
                score -= row['davies_bouldin'] * 10
            
            # Calinski-Harabasz (higher is better, normalize)
            if pd.notna(row['calinski_harabasz']):
                score += np.log1p(row['calinski_harabasz'])
            
            # Penalize noise points
            score -= row['n_noise'] * 0.1
            
            ranks.append(score)
        
        # Convert scores to ranks (1 = best)
        sorted_indices = np.argsort(ranks)[::-1]
        final_ranks = [0] * len(ranks)
        for rank, idx in enumerate(sorted_indices, 1):
            final_ranks[idx] = rank
        
        return final_ranks
