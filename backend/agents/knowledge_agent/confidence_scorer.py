"""
Confidence Scorer for Knowledge Agent
Calculates confidence scores for AI-generated insights and predictions.

This module provides transparency by scoring:
- Data quality impact on insights
- Statistical significance of findings
- Sample size adequacy
- Model certainty in predictions
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level categories."""
    VERY_LOW = "very_low"      # 0-40
    LOW = "low"                # 41-60
    MEDIUM = "medium"          # 61-75
    HIGH = "high"              # 76-90
    VERY_HIGH = "very_high"    # 91-100


class ConfidenceScorer:
    """
    Calculates confidence scores for insights and predictions.
    
    Features:
    - Multi-factor confidence calculation
    - Statistical significance testing
    - Data quality assessment
    - Sample size evaluation
    - Transparent scoring breakdown
    """
    
    def __init__(self):
        """Initialize confidence scorer."""
        self.score_history: List[Dict[str, Any]] = []
    
    def calculate_insight_confidence(
        self,
        insight_type: str,
        data: pd.DataFrame,
        statistical_metrics: Optional[Dict] = None,
        data_quality_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate confidence score for an insight.
        
        Args:
            insight_type: Type of insight (correlation, trend, outlier, etc.)
            data: The dataset being analyzed
            statistical_metrics: Statistical measures related to the insight
            data_quality_score: Overall data quality score (0-100)
            
        Returns:
            Dictionary with confidence score and breakdown
        """
        factors = {}
        
        # Factor 1: Sample Size (0-25 points)
        factors['sample_size'] = self._score_sample_size(len(data))
        
        # Factor 2: Data Quality (0-25 points)
        if data_quality_score is not None:
            factors['data_quality'] = data_quality_score * 0.25
        else:
            factors['data_quality'] = self._score_data_quality(data) * 25
        
        # Factor 3: Statistical Significance (0-30 points)
        factors['statistical_significance'] = self._score_statistical_significance(
            insight_type, statistical_metrics
        )
        
        # Factor 4: Completeness (0-20 points)
        factors['completeness'] = self._score_completeness(data)
        
        # Calculate total confidence
        total_confidence = sum(factors.values())
        
        # Get confidence level
        confidence_level = self._get_confidence_level(total_confidence)
        
        # Generate reasoning
        reasoning = self._generate_confidence_reasoning(
            confidence_level, factors, insight_type
        )
        
        result = {
            'confidence_score': round(total_confidence, 1),
            'confidence_level': confidence_level.value,
            'factors': {k: round(v, 1) for k, v in factors.items()},
            'reasoning': reasoning,
            'recommendations': self._get_recommendations(confidence_level, factors)
        }
        
        # Store in history
        self.score_history.append({
            'insight_type': insight_type,
            **result
        })
        
        return result
    
    def _score_sample_size(self, n: int) -> float:
        """
        Score based on sample size adequacy.
        
        Args:
            n: Number of samples
            
        Returns:
            Score from 0-25
        """
        if n < 30:
            return 5.0  # Very small
        elif n < 100:
            return 12.0  # Small
        elif n < 500:
            return 18.0  # Medium
        elif n < 1000:
            return 22.0  # Good
        else:
            return 25.0  # Excellent
    
    def _score_data_quality(self, data: pd.DataFrame) -> float:
        """
        Score data quality (0-1 scale).
        
        Args:
            data: DataFrame to assess
            
        Returns:
            Quality score from 0-1
        """
        scores = []
        
        # Missing data penalty
        missing_pct = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
        missing_score = max(0, 1 - missing_pct * 2)  # 50% missing = 0 score
        scores.append(missing_score)
        
        # Duplicate rows penalty
        dup_pct = data.duplicated().sum() / len(data)
        dup_score = max(0, 1 - dup_pct * 3)
        scores.append(dup_score)
        
        # Variance score (columns with variance)
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            variances = data[numeric_cols].var()
            zero_var_pct = (variances == 0).sum() / len(variances)
            variance_score = max(0, 1 - zero_var_pct)
            scores.append(variance_score)
        
        return np.mean(scores)
    
    def _score_statistical_significance(
        self,
        insight_type: str,
        metrics: Optional[Dict]
    ) -> float:
        """
        Score statistical significance of insight.
        
        Args:
            insight_type: Type of insight
            metrics: Statistical metrics
            
        Returns:
            Score from 0-30
        """
        if metrics is None:
            return 15.0  # Neutral score
        
        score = 15.0  # Base score
        
        if insight_type == 'correlation':
            # Strong correlation = higher confidence
            corr_value = abs(metrics.get('correlation', 0))
            if corr_value > 0.7:
                score = 28.0
            elif corr_value > 0.5:
                score = 23.0
            elif corr_value > 0.3:
                score = 18.0
            else:
                score = 10.0
        
        elif insight_type == 'trend':
            # Check R-squared or slope significance
            r_squared = metrics.get('r_squared', 0)
            if r_squared > 0.8:
                score = 27.0
            elif r_squared > 0.6:
                score = 22.0
            elif r_squared > 0.4:
                score = 17.0
            else:
                score = 12.0
        
        elif insight_type == 'outlier':
            # Z-score or IQR-based confidence
            n_outliers = metrics.get('n_outliers', 0)
            total_points = metrics.get('total_points', 1)
            outlier_pct = n_outliers / total_points
            
            if 0.01 <= outlier_pct <= 0.05:  # Expected range
                score = 25.0
            elif outlier_pct < 0.01:
                score = 20.0
            else:
                score = 15.0
        
        elif insight_type == 'distribution':
            # Check normality or distribution fit
            p_value = metrics.get('p_value', 0.5)
            if p_value < 0.05:
                score = 26.0
            else:
                score = 18.0
        
        return score
    
    def _score_completeness(self, data: pd.DataFrame) -> float:
        """
        Score data completeness.
        
        Args:
            data: DataFrame to assess
            
        Returns:
            Score from 0-20
        """
        # Missing data percentage
        missing_pct = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
        
        if missing_pct == 0:
            return 20.0
        elif missing_pct < 0.05:
            return 17.0
        elif missing_pct < 0.10:
            return 14.0
        elif missing_pct < 0.20:
            return 10.0
        else:
            return 5.0
    
    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """
        Convert numeric score to confidence level.
        
        Args:
            score: Confidence score (0-100)
            
        Returns:
            ConfidenceLevel enum
        """
        if score >= 91:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 76:
            return ConfidenceLevel.HIGH
        elif score >= 61:
            return ConfidenceLevel.MEDIUM
        elif score >= 41:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _generate_confidence_reasoning(
        self,
        level: ConfidenceLevel,
        factors: Dict[str, float],
        insight_type: str
    ) -> str:
        """
        Generate human-readable confidence reasoning.
        
        Args:
            level: Confidence level
            factors: Score factors
            insight_type: Type of insight
            
        Returns:
            Reasoning string
        """
        reasons = []
        
        # Sample size reasoning
        if factors['sample_size'] >= 22:
            reasons.append("large sample size provides strong statistical power")
        elif factors['sample_size'] >= 18:
            reasons.append("adequate sample size for analysis")
        elif factors['sample_size'] < 12:
            reasons.append("small sample size limits confidence")
        
        # Data quality reasoning
        if factors['data_quality'] >= 20:
            reasons.append("high data quality with minimal issues")
        elif factors['data_quality'] < 15:
            reasons.append("data quality issues may affect reliability")
        
        # Statistical significance
        if factors['statistical_significance'] >= 25:
            reasons.append(f"strong statistical significance for {insight_type}")
        elif factors['statistical_significance'] < 15:
            reasons.append(f"weak statistical evidence for {insight_type}")
        
        # Completeness
        if factors['completeness'] < 12:
            reasons.append("missing data reduces confidence")
        
        confidence_word = {
            ConfidenceLevel.VERY_HIGH: "very confident",
            ConfidenceLevel.HIGH: "confident",
            ConfidenceLevel.MEDIUM: "moderately confident",
            ConfidenceLevel.LOW: "limited confidence",
            ConfidenceLevel.VERY_LOW: "low confidence"
        }
        
        reason_text = ", ".join(reasons)
        return f"I am {confidence_word[level]} in this insight because {reason_text}."
    
    def _get_recommendations(
        self,
        level: ConfidenceLevel,
        factors: Dict[str, float]
    ) -> List[str]:
        """
        Generate recommendations based on confidence factors.
        
        Args:
            level: Confidence level
            factors: Score factors
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if factors['sample_size'] < 18:
            recommendations.append("Collect more data to improve statistical power")
        
        if factors['data_quality'] < 18:
            recommendations.append("Clean data and handle missing values")
        
        if factors['completeness'] < 15:
            recommendations.append("Address missing data through imputation or collection")
        
        if factors['statistical_significance'] < 20:
            recommendations.append("Validate findings with additional statistical tests")
        
        if level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]:
            recommendations.append("⚠️ Use these insights cautiously - consider additional validation")
        
        if not recommendations:
            recommendations.append("✅ Confidence is sufficient for decision-making")
        
        return recommendations
    
    def calculate_prediction_confidence(
        self,
        model_type: str,
        metrics: Dict[str, float],
        data_size: int
    ) -> Dict[str, Any]:
        """
        Calculate confidence for model predictions.
        
        Args:
            model_type: Type of model (classification, regression, etc.)
            metrics: Model performance metrics
            data_size: Size of training data
            
        Returns:
            Confidence score and details
        """
        factors = {}
        
        # Sample size
        factors['sample_size'] = self._score_sample_size(data_size)
        
        # Model performance
        if model_type == 'classification':
            accuracy = metrics.get('accuracy', 0)
            factors['performance'] = accuracy * 40  # 0-40 points
        elif model_type == 'regression':
            r2 = metrics.get('r2', 0)
            factors['performance'] = max(0, r2) * 40
        else:
            factors['performance'] = 20.0  # Neutral
        
        # Cross-validation consistency
        cv_std = metrics.get('cv_std', 0.1)
        if cv_std < 0.05:
            factors['consistency'] = 25.0
        elif cv_std < 0.10:
            factors['consistency'] = 18.0
        else:
            factors['consistency'] = 10.0
        
        # Feature quality
        n_features = metrics.get('n_features', 5)
        if n_features >= 5:
            factors['feature_quality'] = 10.0
        else:
            factors['feature_quality'] = 5.0
        
        total_confidence = sum(factors.values())
        confidence_level = self._get_confidence_level(total_confidence)
        
        return {
            'confidence_score': round(total_confidence, 1),
            'confidence_level': confidence_level.value,
            'factors': {k: round(v, 1) for k, v in factors.items()},
            'reasoning': f"Model confidence based on {model_type} performance and data quality"
        }
    
    def get_score_breakdown(self) -> str:
        """
        Get detailed breakdown of scoring methodology.
        
        Returns:
            Markdown-formatted scoring guide
        """
        return """
## Confidence Scoring Methodology

### Score Components (Total: 100 points)

1. **Sample Size (25 points)**
   - <30 samples: 5 points
   - 30-100: 12 points
   - 100-500: 18 points
   - 500-1000: 22 points
   - >1000: 25 points

2. **Data Quality (25 points)**
   - Based on missing data, duplicates, variance
   - High quality: 20-25 points
   - Medium: 15-20 points
   - Low: <15 points

3. **Statistical Significance (30 points)**
   - Strong evidence: 25-30 points
   - Moderate: 18-25 points
   - Weak: <18 points

4. **Completeness (20 points)**
   - No missing: 20 points
   - <5% missing: 17 points
   - <10% missing: 14 points
   - >20% missing: <10 points

### Confidence Levels

- **Very High (91-100)**: Highly reliable, safe for decisions
- **High (76-90)**: Reliable with minor caveats
- **Medium (61-75)**: Reasonably reliable, use with caution
- **Low (41-60)**: Limited reliability, needs validation
- **Very Low (0-40)**: Not reliable, requires more data
"""
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ConfidenceScorer(scores_calculated={len(self.score_history)})"
