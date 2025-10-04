"""
Feedback System for Knowledge Agent
Enables users to rate insights and improve recommendations over time.

Features:
- Thumbs up/down for insights
- Star ratings (1-5)
- Text feedback and comments
- Feedback analytics
- Learning from user preferences
- Export feedback history
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
import pickle


class FeedbackSystem:
    """
    Manages user feedback on insights and recommendations.
    
    Features:
    - Rate insights (thumbs up/down, stars)
    - Collect text feedback
    - Track feedback history
    - Analyze feedback patterns
    - Export/import feedback data
    - Learn user preferences
    """
    
    def __init__(self, feedback_file: Optional[str] = None):
        """
        Initialize feedback system.
        
        Args:
            feedback_file: Path to load/save feedback history
        """
        self.feedback_history: List[Dict[str, Any]] = []
        self.insight_ratings: Dict[str, List[int]] = defaultdict(list)
        self.category_scores: Dict[str, float] = defaultdict(float)
        self.feedback_file = feedback_file
        
        if feedback_file:
            try:
                self.load_feedback(feedback_file)
            except FileNotFoundError:
                # File doesn't exist yet - will be created on first save
                pass
    
    def add_feedback(
        self,
        insight_id: str,
        insight_text: str,
        rating: int,
        category: str = 'general',
        comment: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Add user feedback for an insight.
        
        Args:
            insight_id: Unique identifier for the insight
            insight_text: The insight being rated
            rating: 1-5 stars (1=poor, 5=excellent) or -1/+1 for thumbs
            category: Category of insight (correlation, trend, outlier, etc.)
            comment: Optional user comment
            metadata: Additional metadata
            
        Returns:
            Feedback entry with ID
        """
        feedback_entry = {
            'id': len(self.feedback_history) + 1,
            'insight_id': insight_id,
            'insight_text': insight_text,
            'rating': rating,
            'category': category,
            'comment': comment,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.feedback_history.append(feedback_entry)
        self.insight_ratings[insight_id].append(rating)
        
        # Update category score (weighted average)
        self._update_category_score(category, rating)
        
        # Auto-save if file specified
        if self.feedback_file:
            self.save_feedback(self.feedback_file)
        
        return feedback_entry
    
    def thumbs_up(self, insight_id: str, insight_text: str, category: str = 'general') -> Dict:
        """Quick thumbs up (+1)."""
        return self.add_feedback(insight_id, insight_text, rating=1, category=category)
    
    def thumbs_down(self, insight_id: str, insight_text: str, category: str = 'general', comment: str = '') -> Dict:
        """Quick thumbs down (-1)."""
        return self.add_feedback(insight_id, insight_text, rating=-1, category=category, comment=comment)
    
    def rate_stars(
        self,
        insight_id: str,
        insight_text: str,
        stars: int,
        category: str = 'general',
        comment: Optional[str] = None
    ) -> Dict:
        """
        Rate insight with 1-5 stars.
        
        Args:
            insight_id: Insight identifier
            insight_text: The insight text
            stars: 1-5 stars
            category: Insight category
            comment: Optional comment
            
        Returns:
            Feedback entry
        """
        if not 1 <= stars <= 5:
            raise ValueError("Stars must be between 1 and 5")
        
        return self.add_feedback(insight_id, insight_text, rating=stars, category=category, comment=comment)
    
    def get_insight_score(self, insight_id: str) -> Dict[str, Any]:
        """
        Get aggregated score for an insight.
        
        Args:
            insight_id: Insight identifier
            
        Returns:
            Score statistics
        """
        if insight_id not in self.insight_ratings:
            return {
                'average_rating': None,
                'total_ratings': 0,
                'positive': 0,
                'negative': 0,
                'sentiment': 'no_feedback'
            }
        
        ratings = self.insight_ratings[insight_id]
        positive = sum(1 for r in ratings if r > 0)
        negative = sum(1 for r in ratings if r < 0)
        
        # Calculate sentiment
        if positive > negative * 2:
            sentiment = 'very_positive'
        elif positive > negative:
            sentiment = 'positive'
        elif negative > positive * 2:
            sentiment = 'very_negative'
        elif negative > positive:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'average_rating': sum(ratings) / len(ratings),
            'total_ratings': len(ratings),
            'positive': positive,
            'negative': negative,
            'sentiment': sentiment,
            'ratings_distribution': Counter(ratings)
        }
    
    def get_category_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics by category.
        
        Returns:
            Category performance statistics
        """
        category_stats = {}
        
        for feedback in self.feedback_history:
            cat = feedback['category']
            if cat not in category_stats:
                category_stats[cat] = {
                    'total_feedback': 0,
                    'ratings': [],
                    'positive': 0,
                    'negative': 0
                }
            
            category_stats[cat]['total_feedback'] += 1
            category_stats[cat]['ratings'].append(feedback['rating'])
            
            if feedback['rating'] > 0:
                category_stats[cat]['positive'] += 1
            else:
                category_stats[cat]['negative'] += 1
        
        # Calculate averages
        for cat, stats in category_stats.items():
            if stats['ratings']:
                stats['average_rating'] = sum(stats['ratings']) / len(stats['ratings'])
                stats['approval_rate'] = stats['positive'] / stats['total_feedback']
            else:
                stats['average_rating'] = 0
                stats['approval_rate'] = 0
        
        return category_stats
    
    def get_top_rated_insights(self, n: int = 10, min_ratings: int = 2) -> List[Dict[str, Any]]:
        """
        Get top-rated insights.
        
        Args:
            n: Number of insights to return
            min_ratings: Minimum number of ratings required
            
        Returns:
            List of top insights with scores
        """
        insight_scores = []
        
        for insight_id, ratings in self.insight_ratings.items():
            if len(ratings) >= min_ratings:
                avg_rating = sum(ratings) / len(ratings)
                
                # Find the insight text
                insight_text = None
                for feedback in self.feedback_history:
                    if feedback['insight_id'] == insight_id:
                        insight_text = feedback['insight_text']
                        break
                
                insight_scores.append({
                    'insight_id': insight_id,
                    'insight_text': insight_text,
                    'average_rating': avg_rating,
                    'total_ratings': len(ratings),
                    'score': self.get_insight_score(insight_id)
                })
        
        # Sort by average rating
        insight_scores.sort(key=lambda x: x['average_rating'], reverse=True)
        
        return insight_scores[:n]
    
    def get_worst_rated_insights(self, n: int = 10, min_ratings: int = 2) -> List[Dict[str, Any]]:
        """Get worst-rated insights to improve."""
        all_scores = self.get_top_rated_insights(n=1000, min_ratings=min_ratings)
        return list(reversed(all_scores))[:n]
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get overall feedback summary.
        
        Returns:
            Summary statistics
        """
        if not self.feedback_history:
            return {
                'total_feedback': 0,
                'average_rating': 0,
                'approval_rate': 0,
                'most_active_category': None
            }
        
        all_ratings = [f['rating'] for f in self.feedback_history]
        positive = sum(1 for r in all_ratings if r > 0)
        
        category_counts = Counter(f['category'] for f in self.feedback_history)
        
        return {
            'total_feedback': len(self.feedback_history),
            'average_rating': sum(all_ratings) / len(all_ratings),
            'approval_rate': positive / len(all_ratings),
            'total_insights_rated': len(self.insight_ratings),
            'most_active_category': category_counts.most_common(1)[0] if category_counts else None,
            'category_distribution': dict(category_counts),
            'feedback_with_comments': sum(1 for f in self.feedback_history if f.get('comment'))
        }
    
    def get_recommendations_for_improvement(self) -> List[str]:
        """
        Get recommendations based on feedback patterns.
        
        Returns:
            List of improvement recommendations
        """
        recommendations = []
        
        category_perf = self.get_category_performance()
        
        # Find underperforming categories
        for cat, stats in category_perf.items():
            if stats['average_rating'] < 0 or stats['approval_rate'] < 0.4:
                recommendations.append(
                    f"⚠️ Improve {cat} insights - current approval rate: {stats['approval_rate']:.1%}"
                )
        
        # Check for categories with high variance
        for cat, stats in category_perf.items():
            if stats['total_feedback'] >= 5:
                variance = sum((r - stats['average_rating']) ** 2 for r in stats['ratings']) / len(stats['ratings'])
                if variance > 2:
                    recommendations.append(
                        f"📊 {cat} insights have inconsistent quality - standardize approach"
                    )
        
        # Overall feedback volume
        summary = self.get_feedback_summary()
        if summary['total_feedback'] < 10:
            recommendations.append("💡 Collect more feedback to improve recommendations")
        
        if not recommendations:
            recommendations.append("✅ Feedback quality is good - keep up the great work!")
        
        return recommendations
    
    def _update_category_score(self, category: str, rating: int) -> None:
        """Update weighted category score."""
        current_score = self.category_scores[category]
        # Exponential moving average (alpha = 0.3)
        self.category_scores[category] = 0.3 * rating + 0.7 * current_score
    
    def save_feedback(self, filepath: str) -> None:
        """
        Save feedback history to file.
        
        Args:
            filepath: Path to save feedback (JSON or pickle)
        """
        data = {
            'feedback_history': self.feedback_history,
            'insight_ratings': {k: list(v) for k, v in self.insight_ratings.items()},
            'category_scores': dict(self.category_scores),
            'metadata': {
                'total_feedback': len(self.feedback_history),
                'last_updated': datetime.now().isoformat()
            }
        }
        
        if filepath.endswith('.json'):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
    
    def load_feedback(self, filepath: str) -> None:
        """
        Load feedback history from file.
        
        Args:
            filepath: Path to feedback file
        """
        if filepath.endswith('.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
        
        self.feedback_history = data.get('feedback_history', [])
        self.insight_ratings = defaultdict(list, {
            k: list(v) for k, v in data.get('insight_ratings', {}).items()
        })
        self.category_scores = defaultdict(float, data.get('category_scores', {}))
    
    def export_for_analysis(self, filepath: str) -> None:
        """
        Export feedback in analysis-friendly format (CSV).
        
        Args:
            filepath: Path to save CSV
        """
        import pandas as pd
        
        df = pd.DataFrame(self.feedback_history)
        df.to_csv(filepath, index=False)
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """
        Learn user preferences from feedback patterns.
        
        Returns:
            Preference dictionary
        """
        category_perf = self.get_category_performance()
        
        # Sort categories by approval rate
        sorted_cats = sorted(
            category_perf.items(),
            key=lambda x: x[1].get('approval_rate', 0),
            reverse=True
        )
        
        return {
            'preferred_categories': [cat for cat, _ in sorted_cats[:3]],
            'disliked_categories': [cat for cat, _ in sorted_cats[-3:]],
            'category_scores': self.category_scores,
            'total_feedback_given': len(self.feedback_history)
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"FeedbackSystem("
            f"total_feedback={len(self.feedback_history)}, "
            f"insights_rated={len(self.insight_ratings)}, "
            f"categories={len(self.category_scores)})"
        )
