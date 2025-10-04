"""
Query Engine Module
Handles natural language questions about data using Pandas queries
and caching for fast responses.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime
import json


class QueryEngine:
    """
    Executes queries on data and caches results for fast follow-up questions.
    Combines Pandas operations with smart query interpretation.
    """
    
    def __init__(self):
        """Initialize the Query Engine"""
        self.query_cache = {}
        self.data = None
        self.profile_data = None
        
    def set_data(self, data: pd.DataFrame, profile_data: Optional[Dict[str, Any]] = None):
        """
        Set the dataset and optional profile data.
        
        Args:
            data: DataFrame to query
            profile_data: Optional profiling data from DataProfiler
        """
        self.data = data.copy()
        self.profile_data = profile_data
        self.query_cache = {}  # Clear cache when new data is loaded
    
    def query(self, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Execute a natural language query on the data.
        
        Args:
            question: Natural language question
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with answer, query details, and visualization suggestions
        """
        # Check cache
        question_key = question.lower().strip()
        if use_cache and question_key in self.query_cache:
            cached_result = self.query_cache[question_key].copy()
            cached_result['from_cache'] = True
            return cached_result
        
        # Parse question and execute
        query_type = self._classify_question(question)
        result = self._execute_query(question, query_type)
        
        # Cache result
        self.query_cache[question_key] = result
        result['from_cache'] = False
        
        return result
    
    def _classify_question(self, question: str) -> str:
        """
        Classify the type of question being asked.
        
        Returns:
            Question type: 'aggregation', 'filtering', 'comparison', 'statistical', 
                          'top_n', 'distribution', 'correlation', 'temporal'
        """
        question_lower = question.lower()
        
        # Top N queries
        if any(word in question_lower for word in ['top', 'bottom', 'highest', 'lowest', 'largest', 'smallest', 'best', 'worst']):
            return 'top_n'
        
        # Aggregation queries
        if any(word in question_lower for word in ['total', 'sum', 'average', 'mean', 'count', 'how many']):
            return 'aggregation'
        
        # Temporal queries
        if any(word in question_lower for word in ['month', 'year', 'day', 'week', 'quarter', 'date', 'time', 'when']):
            return 'temporal'
        
        # Correlation queries
        if any(word in question_lower for word in ['relationship', 'correlation', 'related', 'affect', 'impact']):
            return 'correlation'
        
        # Distribution queries
        if any(word in question_lower for word in ['distribution', 'spread', 'range', 'variance']):
            return 'distribution'
        
        # Comparison queries
        if any(word in question_lower for word in ['compare', 'difference', 'vs', 'versus', 'between']):
            return 'comparison'
        
        # Filtering queries
        if any(word in question_lower for word in ['where', 'filter', 'only', 'specific']):
            return 'filtering'
        
        # Statistical queries
        if any(word in question_lower for word in ['median', 'percentile', 'quartile', 'std', 'deviation']):
            return 'statistical'
        
        return 'general'
    
    def _execute_query(self, question: str, query_type: str) -> Dict[str, Any]:
        """Execute the appropriate query based on type"""
        
        if self.data is None:
            return {
                'answer': 'No data loaded. Please load data first.',
                'query_type': query_type,
                'success': False
            }
        
        try:
            if query_type == 'top_n':
                return self._handle_top_n_query(question)
            elif query_type == 'aggregation':
                return self._handle_aggregation_query(question)
            elif query_type == 'temporal':
                return self._handle_temporal_query(question)
            elif query_type == 'correlation':
                return self._handle_correlation_query(question)
            elif query_type == 'distribution':
                return self._handle_distribution_query(question)
            elif query_type == 'comparison':
                return self._handle_comparison_query(question)
            elif query_type == 'statistical':
                return self._handle_statistical_query(question)
            else:
                return self._handle_general_query(question)
                
        except Exception as e:
            return {
                'answer': f'Error executing query: {str(e)}',
                'query_type': query_type,
                'success': False,
                'error': str(e)
            }
    
    def _handle_top_n_query(self, question: str) -> Dict[str, Any]:
        """Handle top N / bottom N queries"""
        # Extract number (default to 5)
        numbers = re.findall(r'\d+', question)
        n = int(numbers[0]) if numbers else 5
        
        # Determine ascending or descending
        ascending = any(word in question.lower() for word in ['bottom', 'lowest', 'smallest', 'worst'])
        
        # Find relevant columns
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        
        # Try to identify the measure column from question
        measure_col = None
        for col in numeric_cols:
            if col.lower() in question.lower():
                measure_col = col
                break
        
        if measure_col is None and len(numeric_cols) > 0:
            # Default to first numeric column
            measure_col = numeric_cols[0]
        
        if measure_col is None:
            return {
                'answer': 'No numeric column found to rank by.',
                'query_type': 'top_n',
                'success': False
            }
        
        # Find grouping column (categorical or object type)
        cat_cols = self.data.select_dtypes(include=['object', 'category']).columns
        group_col = None
        
        for col in cat_cols:
            if col.lower() in question.lower() and col != measure_col:
                group_col = col
                break
        
        # Execute query
        if group_col:
            # Grouped top N
            result_df = self.data.groupby(group_col)[measure_col].sum().sort_values(ascending=ascending).head(n)
            answer = f"Top {n} {group_col} by {measure_col}:\n"
            for idx, (category, value) in enumerate(result_df.items(), 1):
                answer += f"{idx}. {category}: {value:,.2f}\n"
        else:
            # Simple top N rows
            result_df = self.data.nlargest(n, measure_col) if not ascending else self.data.nsmallest(n, measure_col)
            answer = f"Top {n} rows by {measure_col}:\n"
            answer += result_df[[measure_col]].to_string()
        
        return {
            'answer': answer.strip(),
            'query_type': 'top_n',
            'success': True,
            'data': result_df.to_dict() if isinstance(result_df, pd.Series) else result_df.to_dict('records'),
            'visualization_suggestion': {
                'type': 'bar_chart',
                'x': group_col if group_col else 'index',
                'y': measure_col
            }
        }
    
    def _handle_aggregation_query(self, question: str) -> Dict[str, Any]:
        """Handle aggregation queries (sum, average, count, etc.)"""
        question_lower = question.lower()
        
        # Determine aggregation function
        if 'sum' in question_lower or 'total' in question_lower:
            agg_func = 'sum'
        elif 'average' in question_lower or 'mean' in question_lower:
            agg_func = 'mean'
        elif 'count' in question_lower or 'how many' in question_lower:
            agg_func = 'count'
        elif 'max' in question_lower or 'maximum' in question_lower:
            agg_func = 'max'
        elif 'min' in question_lower or 'minimum' in question_lower:
            agg_func = 'min'
        else:
            agg_func = 'sum'  # Default
        
        # Find numeric columns
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        
        # Try to identify the column
        target_col = None
        for col in numeric_cols:
            if col.lower() in question_lower:
                target_col = col
                break
        
        if target_col is None and len(numeric_cols) > 0:
            target_col = numeric_cols[0]
        
        if target_col is None:
            return {
                'answer': 'No numeric column found for aggregation.',
                'query_type': 'aggregation',
                'success': False
            }
        
        # Check for grouping
        cat_cols = self.data.select_dtypes(include=['object', 'category']).columns
        group_col = None
        
        for col in cat_cols:
            if col.lower() in question_lower and col != target_col:
                group_col = col
                break
        
        # Execute aggregation
        if group_col:
            result = self.data.groupby(group_col)[target_col].agg(agg_func)
            answer = f"{agg_func.capitalize()} of {target_col} by {group_col}:\n"
            for category, value in result.items():
                answer += f"  {category}: {value:,.2f}\n"
            data = result.to_dict()
        else:
            result = getattr(self.data[target_col], agg_func)()
            answer = f"The {agg_func} of {target_col} is {result:,.2f}"
            data = {target_col: float(result)}
        
        return {
            'answer': answer.strip(),
            'query_type': 'aggregation',
            'success': True,
            'data': data,
            'aggregation': agg_func,
            'column': target_col
        }
    
    def _handle_temporal_query(self, question: str) -> Dict[str, Any]:
        """Handle temporal/time-based queries"""
        datetime_cols = self.data.select_dtypes(include=['datetime64']).columns
        
        if len(datetime_cols) == 0:
            return {
                'answer': 'No datetime columns found in the dataset.',
                'query_type': 'temporal',
                'success': False
            }
        
        date_col = datetime_cols[0]  # Use first datetime column
        
        # Find numeric column to analyze
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        value_col = None
        
        for col in numeric_cols:
            if col.lower() in question.lower():
                value_col = col
                break
        
        if value_col is None and len(numeric_cols) > 0:
            value_col = numeric_cols[0]
        
        # Determine time grouping
        question_lower = question.lower()
        if 'month' in question_lower:
            group_freq = 'M'
            group_name = 'month'
        elif 'year' in question_lower:
            group_freq = 'Y'
            group_name = 'year'
        elif 'week' in question_lower:
            group_freq = 'W'
            group_name = 'week'
        elif 'day' in question_lower:
            group_freq = 'D'
            group_name = 'day'
        elif 'quarter' in question_lower:
            group_freq = 'Q'
            group_name = 'quarter'
        else:
            group_freq = 'M'
            group_name = 'month'
        
        # Determine aggregation
        if 'highest' in question_lower or 'maximum' in question_lower:
            agg_func = 'max'
        elif 'lowest' in question_lower or 'minimum' in question_lower:
            agg_func = 'min'
        elif 'average' in question_lower:
            agg_func = 'mean'
        else:
            agg_func = 'sum'
        
        # Group by time and aggregate
        if value_col:
            result = self.data.groupby(pd.Grouper(key=date_col, freq=group_freq))[value_col].agg(agg_func)
            
            # Find the period with highest/lowest value
            if 'highest' in question_lower or 'maximum' in question_lower:
                best_period = result.idxmax()
                best_value = result.max()
                answer = f"The {group_name} with the highest {value_col} is {best_period.strftime('%Y-%m')} with {best_value:,.2f}"
            elif 'lowest' in question_lower or 'minimum' in question_lower:
                best_period = result.idxmin()
                best_value = result.min()
                answer = f"The {group_name} with the lowest {value_col} is {best_period.strftime('%Y-%m')} with {best_value:,.2f}"
            else:
                answer = f"{value_col} by {group_name}:\n"
                for period, value in result.tail(12).items():  # Last 12 periods
                    answer += f"  {period.strftime('%Y-%m')}: {value:,.2f}\n"
        else:
            # Just count by period
            result = self.data.groupby(pd.Grouper(key=date_col, freq=group_freq)).size()
            answer = f"Record count by {group_name}:\n"
            for period, count in result.tail(12).items():
                answer += f"  {period.strftime('%Y-%m')}: {count}\n"
        
        return {
            'answer': answer.strip(),
            'query_type': 'temporal',
            'success': True,
            'data': result.to_dict(),
            'visualization_suggestion': {
                'type': 'line_chart',
                'x': date_col,
                'y': value_col if value_col else 'count'
            }
        }
    
    def _handle_correlation_query(self, question: str) -> Dict[str, Any]:
        """Handle correlation/relationship queries"""
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {
                'answer': 'Need at least 2 numeric columns to analyze relationships.',
                'query_type': 'correlation',
                'success': False
            }
        
        # Try to identify columns from question
        mentioned_cols = []
        for col in numeric_cols:
            if col.lower() in question.lower():
                mentioned_cols.append(col)
        
        if len(mentioned_cols) >= 2:
            col1, col2 = mentioned_cols[0], mentioned_cols[1]
        else:
            # Use first two numeric columns
            col1, col2 = numeric_cols[0], numeric_cols[1]
        
        # Calculate correlation
        correlation = self.data[col1].corr(self.data[col2])
        
        # Interpret correlation
        if abs(correlation) > 0.7:
            strength = "strong"
        elif abs(correlation) > 0.4:
            strength = "moderate"
        else:
            strength = "weak"
        
        direction = "positive" if correlation > 0 else "negative"
        
        answer = f"There is a {strength} {direction} correlation (r={correlation:.3f}) between {col1} and {col2}."
        
        if abs(correlation) > 0.7:
            answer += f" This suggests that as {col1} {'increases' if correlation > 0 else 'decreases'}, {col2} tends to {'increase' if correlation > 0 else 'decrease'} as well."
        
        return {
            'answer': answer,
            'query_type': 'correlation',
            'success': True,
            'correlation': float(correlation),
            'variables': [col1, col2],
            'visualization_suggestion': {
                'type': 'scatter_plot',
                'x': col1,
                'y': col2
            }
        }
    
    def _handle_distribution_query(self, question: str) -> Dict[str, Any]:
        """Handle distribution queries"""
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        
        # Find column mentioned in question
        target_col = None
        for col in numeric_cols:
            if col.lower() in question.lower():
                target_col = col
                break
        
        if target_col is None and len(numeric_cols) > 0:
            target_col = numeric_cols[0]
        
        if target_col is None:
            return {
                'answer': 'No numeric column found for distribution analysis.',
                'query_type': 'distribution',
                'success': False
            }
        
        # Calculate distribution statistics
        stats = self.data[target_col].describe()
        
        answer = f"Distribution of {target_col}:\n"
        answer += f"  Mean: {stats['mean']:,.2f}\n"
        answer += f"  Median: {stats['50%']:,.2f}\n"
        answer += f"  Std Dev: {stats['std']:,.2f}\n"
        answer += f"  Range: {stats['min']:,.2f} to {stats['max']:,.2f}\n"
        answer += f"  IQR: {stats['75%'] - stats['25%']:,.2f}"
        
        return {
            'answer': answer,
            'query_type': 'distribution',
            'success': True,
            'statistics': stats.to_dict(),
            'column': target_col,
            'visualization_suggestion': {
                'type': 'histogram',
                'column': target_col
            }
        }
    
    def _handle_comparison_query(self, question: str) -> Dict[str, Any]:
        """Handle comparison queries"""
        return {
            'answer': 'Comparison queries are being processed. Please provide specific values to compare.',
            'query_type': 'comparison',
            'success': True
        }
    
    def _handle_statistical_query(self, question: str) -> Dict[str, Any]:
        """Handle statistical queries"""
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        
        # Find target column
        target_col = None
        for col in numeric_cols:
            if col.lower() in question.lower():
                target_col = col
                break
        
        if target_col is None and len(numeric_cols) > 0:
            target_col = numeric_cols[0]
        
        if target_col is None:
            return {
                'answer': 'No numeric column found for statistical analysis.',
                'query_type': 'statistical',
                'success': False
            }
        
        # Calculate requested statistic
        question_lower = question.lower()
        
        if 'median' in question_lower:
            result = self.data[target_col].median()
            answer = f"The median of {target_col} is {result:,.2f}"
        elif 'std' in question_lower or 'deviation' in question_lower:
            result = self.data[target_col].std()
            answer = f"The standard deviation of {target_col} is {result:,.2f}"
        elif 'percentile' in question_lower or 'quartile' in question_lower:
            q25 = self.data[target_col].quantile(0.25)
            q50 = self.data[target_col].quantile(0.50)
            q75 = self.data[target_col].quantile(0.75)
            answer = f"Quartiles for {target_col}:\n  25th: {q25:,.2f}\n  50th: {q50:,.2f}\n  75th: {q75:,.2f}"
            result = {'25th': q25, '50th': q50, '75th': q75}
        else:
            result = self.data[target_col].describe().to_dict()
            answer = f"Statistics for {target_col}:\n{self.data[target_col].describe().to_string()}"
        
        return {
            'answer': answer,
            'query_type': 'statistical',
            'success': True,
            'result': result if isinstance(result, (dict, float, int)) else float(result),
            'column': target_col
        }
    
    def _handle_general_query(self, question: str) -> Dict[str, Any]:
        """Handle general queries"""
        answer = f"I can help answer questions about the data. Try asking about:\n"
        answer += "- Top/bottom values (e.g., 'What are the top 5 products by sales?')\n"
        answer += "- Aggregations (e.g., 'What is the total revenue?')\n"
        answer += "- Time-based queries (e.g., 'Which month had the highest sales?')\n"
        answer += "- Correlations (e.g., 'Is there a relationship between price and quantity?')\n"
        answer += "- Distributions (e.g., 'What is the distribution of age?')"
        
        return {
            'answer': answer,
            'query_type': 'general',
            'success': True,
            'suggestion': 'Try being more specific about what you want to know'
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the query cache"""
        return {
            'cached_queries': len(self.query_cache),
            'cache_keys': list(self.query_cache.keys())
        }
    
    def clear_cache(self):
        """Clear the query cache"""
        self.query_cache = {}
