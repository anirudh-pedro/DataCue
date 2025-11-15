"""
Query Engine Module
Handles natural language questions about data using LLM-powered analysis.
Combines Pandas operations with Groq AI for intelligent responses.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime, date
import json
import os
from groq import Groq
from core.config import get_settings


def json_serializable(obj):
    """Convert non-JSON-serializable objects to serializable format."""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    return obj


class QueryEngine:
    """
    Executes queries on data and caches results for fast follow-up questions.
    Uses Groq LLM for intelligent, context-aware responses.
    """
    
    def __init__(self):
        """Initialize the Query Engine with Groq client and configuration"""
        self.query_cache = {}
        self.data = None
        self.profile_data = None
        
        # Load settings
        self.settings = get_settings()
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=self.settings.groq_api_key) if self.settings.groq_api_key else None
        self.model = self.settings.llm_model
        
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
        Execute a natural language query on the data using LLM.
        
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
        
        # Use LLM-powered query if Groq is available
        if self.groq_client:
            result = self._llm_powered_query(question)
        else:
            # Fallback to rule-based query
            query_type = self._classify_question(question)
            result = self._execute_query(question, query_type)
        
        # Cache result
        self.query_cache[question_key] = result
        result['from_cache'] = False
        
        return result
    
    def _llm_powered_query(self, question: str) -> Dict[str, Any]:
        """
        Use Groq LLM to answer questions about the data intelligently.
        
        Args:
            question: User's natural language question
            
        Returns:
            Dictionary with LLM-generated answer and data analysis
        """
        if self.data is None:
            return {
                'answer': 'No data loaded. Please load data first.',
                'query_type': 'llm',
                'success': False
            }
        
        try:
            # Prepare dataset summary for LLM (with intelligent column selection)
            dataset_context = self._prepare_dataset_context(question)
            
            # Analyze question and compute relevant data
            computed_data = self._compute_data_for_question(question)
            
            # Build prompt for LLM
            prompt = self._build_llm_prompt(question, dataset_context, computed_data)
            
            # Call Groq API
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data analyst assistant. Answer questions about datasets clearly and concisely. Use the provided data context and statistics to give accurate answers. Format numbers nicely. Be direct and helpful."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                'answer': answer,
                'query_type': 'llm',
                'success': True,
                'data': computed_data.get('data', {}),
                'visualization_suggestion': computed_data.get('viz_suggestion')
            }
            
        except Exception as e:
            # Fallback to rule-based query on error
            print(f"LLM query failed: {e}, falling back to rule-based")
            query_type = self._classify_question(question)
            return self._execute_query(question, query_type)
    
    def _prepare_dataset_context(self, question: str = "") -> str:
        """Prepare a concise summary of the dataset for LLM context.
        
        Args:
            question: The user's question (used to select relevant columns)
        """
        num_rows, num_cols = self.data.shape
        columns = self.data.columns.tolist()
        dtypes = self.data.dtypes.to_dict()
        
        # Get sample statistics for numeric columns
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        numeric_stats = {}
        max_cols = self.settings.max_numeric_columns_context
        
        # INTELLIGENT SELECTION: Prioritize columns mentioned in the question
        question_lower = question.lower() if question else ""
        relevant_numeric_cols = []
        other_numeric_cols = []
        
        for col in numeric_cols:
            if col.lower() in question_lower:
                relevant_numeric_cols.append(col)
            else:
                other_numeric_cols.append(col)
        
        # Take relevant columns first, then fill with others up to max_cols
        selected_numeric_cols = relevant_numeric_cols + other_numeric_cols
        selected_numeric_cols = selected_numeric_cols[:max_cols]
        
        for col in selected_numeric_cols:
            numeric_stats[col] = {
                'mean': float(round(self.data[col].mean(), 2)),
                'min': float(round(self.data[col].min(), 2)),
                'max': float(round(self.data[col].max(), 2))
            }
        
        # Get sample values for categorical columns
        cat_cols = self.data.select_dtypes(include=['object', 'category']).columns
        cat_info = {}
        max_cat_cols = self.settings.max_categorical_columns_context
        max_unique = self.settings.max_unique_values_display
        
        # INTELLIGENT SELECTION: Prioritize categorical columns mentioned in question
        relevant_cat_cols = []
        other_cat_cols = []
        
        for col in cat_cols:
            if col.lower() in question_lower:
                relevant_cat_cols.append(col)
            else:
                other_cat_cols.append(col)
        
        # Take relevant columns first, then fill with others
        selected_cat_cols = relevant_cat_cols + other_cat_cols
        selected_cat_cols = selected_cat_cols[:max_cat_cols]
        
        for col in selected_cat_cols:
            unique_vals = self.data[col].unique()[:max_unique]
            cat_info[col] = {
                'unique_count': int(self.data[col].nunique()),
                'sample_values': [str(v) for v in unique_vals]
            }
        
        context = f"""Dataset Overview:
- Rows: {num_rows:,}
- Columns: {num_cols}
- Column names: {', '.join(columns)}

Numeric Columns Summary:
{json.dumps(numeric_stats, indent=2)}

Categorical Columns Summary:
{json.dumps(cat_info, indent=2)}
"""
        
        # Optionally include sample data or full dataset
        if self.settings.include_sample_data or num_rows <= self.settings.max_full_dataset_rows:
            # Convert DataFrame to dict and handle special types
            if num_rows <= self.settings.max_full_dataset_rows:
                # For small datasets, send entire dataset
                sample_df = self.data.head(num_rows).copy()
                # Convert datetime columns to strings
                for col in sample_df.select_dtypes(include=['datetime64']).columns:
                    sample_df[col] = sample_df[col].astype(str)
                sample_data = sample_df.to_dict('records')
                # Clean any remaining non-serializable objects
                sample_data = json.loads(json.dumps(sample_data, default=json_serializable))
                context += f"\n\nFull Dataset (all {num_rows} rows):\n{json.dumps(sample_data, indent=2)}\n"
            else:
                # For large datasets, send sample rows
                sample_df = self.data.head(self.settings.max_sample_rows).copy()
                # Convert datetime columns to strings
                for col in sample_df.select_dtypes(include=['datetime64']).columns:
                    sample_df[col] = sample_df[col].astype(str)
                sample_data = sample_df.to_dict('records')
                # Clean any remaining non-serializable objects
                sample_data = json.loads(json.dumps(sample_data, default=json_serializable))
                context += f"\n\nSample Data (first {self.settings.max_sample_rows} rows):\n{json.dumps(sample_data, indent=2)}\n"
        
        return context
    
    def _compute_data_for_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze the question and compute relevant statistics.
        
        Returns computed data and visualization suggestions.
        """
        question_lower = question.lower()
        result = {'data': {}, 'viz_suggestion': None}
        
        # Detect user-provided values for calculations
        # Pattern: "profit margin is 200" or "threshold is 100" or "target = 50"
        value_patterns = [
            (r'profit\s+margin\s+(?:is|=)\s+(\d+(?:\.\d+)?)', 'profit_margin'),
            (r'threshold\s+(?:is|=)\s+(\d+(?:\.\d+)?)', 'threshold'),
            (r'target\s+(?:is|=)\s+(\d+(?:\.\d+)?)', 'target'),
            (r'limit\s+(?:is|=)\s+(\d+(?:\.\d+)?)', 'limit'),
        ]
        
        for pattern, param_name in value_patterns:
            match = re.search(pattern, question_lower)
            if match:
                param_value = float(match.group(1))
                result['data'][f'user_provided_{param_name}'] = param_value
                
                # If profit margin is provided, calculate derived metrics
                if param_name == 'profit_margin':
                    numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                    
                    # Look for revenue and units_sold columns
                    revenue_cols = [col for col in numeric_cols if 'revenue' in col.lower()]
                    units_cols = [col for col in numeric_cols if 'unit' in col.lower() and 'sold' in col.lower()]
                    
                    if revenue_cols and units_cols:
                        revenue_col = revenue_cols[0]
                        units_col = units_cols[0]
                        
                        # Calculate profit = revenue - (units_sold * unit_cost_implied)
                        # If profit_margin is given, we can find which records exceed it
                        # Assuming profit = revenue - cost, and margin is the threshold
                        
                        # Simple interpretation: Find rows where revenue > profit_margin
                        filtered_data = self.data[self.data[revenue_col] > param_value]
                        
                        result['data']['records_exceeding_profit_margin'] = int(len(filtered_data))
                        result['data']['profit_margin_threshold'] = param_value
                        
                        if len(filtered_data) > 0:
                            # Get the units_sold values that exceed the margin
                            exceeding_units = filtered_data[units_col].tolist()
                            result['data']['units_sold_exceeding_margin'] = [int(u) for u in exceeding_units[:20]]  # Limit to 20
                            result['data']['total_units_exceeding'] = int(filtered_data[units_col].sum())
                            result['data']['avg_units_exceeding'] = float(round(filtered_data[units_col].mean(), 2))
        
        # Detect "first N" or "last N" row-level queries
        first_n_match = re.search(r'first\s+(\d+)', question_lower)
        last_n_match = re.search(r'last\s+(\d+)', question_lower)
        
        if first_n_match or last_n_match:
            n = int(first_n_match.group(1) if first_n_match else last_n_match.group(1))
            is_first = first_n_match is not None
            
            # Find which column is being asked about - use word boundaries to avoid partial matches
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns
            
            # Prioritize columns explicitly mentioned in the question (with word boundaries)
            target_col = None
            best_match_len = 0
            
            for col in numeric_cols:
                # Use word boundary or underscore/space separation to avoid false matches
                # Example: "age" should not match in "average", but should match "age column"
                col_pattern = r'\b' + re.escape(col.lower()) + r'\b'
                if re.search(col_pattern, question_lower):
                    # Prefer longer matches (more specific)
                    if len(col) > best_match_len:
                        target_col = col
                        best_match_len = len(col)
            
            # If we found a target column, compute first/last N statistics
            if target_col:
                if is_first:
                    values = self.data[target_col].head(n).tolist()
                    result['data'][f'{target_col}_first_{n}_values'] = [float(round(v, 2)) for v in values]
                    result['data'][f'{target_col}_first_{n}_average'] = float(round(self.data[target_col].head(n).mean(), 2))
                    result['data'][f'{target_col}_first_{n}_sum'] = float(round(self.data[target_col].head(n).sum(), 2))
                else:
                    values = self.data[target_col].tail(n).tolist()
                    result['data'][f'{target_col}_last_{n}_values'] = [float(round(v, 2)) for v in values]
                    result['data'][f'{target_col}_last_{n}_average'] = float(round(self.data[target_col].tail(n).mean(), 2))
                    result['data'][f'{target_col}_last_{n}_sum'] = float(round(self.data[target_col].tail(n).sum(), 2))
        
        # Detect categorical filtering (e.g., "how many males")
        cat_cols = self.data.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            unique_values = self.data[col].unique()
            for value in unique_values:
                if str(value).lower() in question_lower:
                    # Count for this category
                    count = int(len(self.data[self.data[col] == value]))
                    result['data'][f'{col}_{value}_count'] = count
                    # Convert value_counts to regular dict with int values
                    distribution = {str(k): int(v) for k, v in self.data[col].value_counts().items()}
                    result['data'][f'{col}_distribution'] = distribution
                    result['viz_suggestion'] = {
                        'type': 'bar_chart',
                        'x': col,
                        'y': 'count'
                    }
        
        # Detect numeric aggregations
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col.lower() in question_lower:
                result['data'][f'{col}_sum'] = float(round(self.data[col].sum(), 2))
                result['data'][f'{col}_mean'] = float(round(self.data[col].mean(), 2))
                result['data'][f'{col}_min'] = float(round(self.data[col].min(), 2))
                result['data'][f'{col}_max'] = float(round(self.data[col].max(), 2))
                result['data'][f'{col}_count'] = int(self.data[col].count())
        
        # Metadata questions
        if any(word in question_lower for word in ['column', 'field', 'attribute']):
            result['data']['total_columns'] = int(len(self.data.columns))
            result['data']['column_names'] = self.data.columns.tolist()
        
        if any(word in question_lower for word in ['row', 'record', 'entry']):
            result['data']['total_rows'] = int(len(self.data))
        
        return result
    
    def _build_llm_prompt(self, question: str, dataset_context: str, computed_data: Dict[str, Any]) -> str:
        """Build the prompt for LLM with question, context, and computed data."""
        
        computed_stats = json.dumps(computed_data.get('data', {}), indent=2)
        
        prompt = f"""Question: {question}

{dataset_context}

Computed Statistics for this Question:
{computed_stats}

Instructions:
1. Answer the question directly and concisely
2. Use the computed statistics provided
3. Format numbers with commas for readability (e.g., 1,234 not 1234)
4. Be specific and accurate
5. If asking about counts, give the exact number
6. If the data doesn't contain the answer, say so clearly

Answer:"""
        
        return prompt
    
    def _classify_question(self, question: str) -> str:
        """
        Classify the type of question being asked.
        
        Returns:
            Question type: 'aggregation', 'filtering', 'comparison', 'statistical', 
                          'top_n', 'distribution', 'correlation', 'temporal', 'metadata'
        """
        question_lower = question.lower()
        
        # Metadata/Schema queries (check FIRST before aggregation)
        metadata_patterns = [
            r'(how many|what|total|number of)\s+(columns?|fields?|attributes?)',
            r'(how many|what|total|number of)\s+(rows?|records?|entries?|samples?)',
            r'(what|show|list|display)\s+(columns?|fields?|attributes?)',
            r'(dataset|data)\s+(size|shape|dimensions?)',
            r'(column|field)\s+(names?|list)',
        ]
        for pattern in metadata_patterns:
            if re.search(pattern, question_lower):
                return 'metadata'
        
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
            if query_type == 'metadata':
                return self._handle_metadata_query(question)
            elif query_type == 'top_n':
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
    
    def _handle_metadata_query(self, question: str) -> Dict[str, Any]:
        """Handle metadata/schema queries about the dataset structure"""
        question_lower = question.lower()
        
        # Determine what metadata is being asked
        if re.search(r'(how many|what|total|number of)\s+(columns?|fields?|attributes?)', question_lower):
            # Number of columns
            num_columns = len(self.data.columns)
            column_list = ', '.join(self.data.columns.tolist())
            answer = f"The dataset has **{num_columns} columns**: {column_list}"
            
            return {
                'answer': answer,
                'query_type': 'metadata',
                'success': True,
                'data': {
                    'total_columns': num_columns,
                    'columns': self.data.columns.tolist(),
                    'dtypes': self.data.dtypes.astype(str).to_dict()
                },
                'visualization_suggestion': None
            }
        
        elif re.search(r'(how many|what|total|number of)\s+(rows?|records?|entries?|samples?)', question_lower):
            # Number of rows
            num_rows = len(self.data)
            answer = f"The dataset has **{num_rows:,} rows** (records)."
            
            return {
                'answer': answer,
                'query_type': 'metadata',
                'success': True,
                'data': {
                    'total_rows': num_rows,
                    'total_columns': len(self.data.columns)
                },
                'visualization_suggestion': None
            }
        
        elif re.search(r'(dataset|data)\s+(size|shape|dimensions?)', question_lower):
            # Dataset shape
            num_rows, num_columns = self.data.shape
            memory_usage = self.data.memory_usage(deep=True).sum() / 1024**2  # MB
            answer = f"**Dataset dimensions**: {num_rows:,} rows × {num_columns} columns\n"
            answer += f"**Memory usage**: {memory_usage:.2f} MB"
            
            return {
                'answer': answer,
                'query_type': 'metadata',
                'success': True,
                'data': {
                    'rows': num_rows,
                    'columns': num_columns,
                    'memory_mb': round(memory_usage, 2)
                },
                'visualization_suggestion': None
            }
        
        elif re.search(r'(column|field)\s+(names?|list)', question_lower) or 'show' in question_lower and 'column' in question_lower:
            # List column names
            columns = self.data.columns.tolist()
            dtypes = self.data.dtypes.astype(str).to_dict()
            
            answer = f"**{len(columns)} columns in the dataset:**\n\n"
            for col in columns:
                dtype = dtypes.get(col, 'unknown')
                answer += f"• **{col}** ({dtype})\n"
            
            return {
                'answer': answer.strip(),
                'query_type': 'metadata',
                'success': True,
                'data': {
                    'columns': columns,
                    'dtypes': dtypes
                },
                'visualization_suggestion': None
            }
        
        else:
            # General metadata
            num_rows, num_columns = self.data.shape
            answer = f"**Dataset Overview:**\n"
            answer += f"• Rows: {num_rows:,}\n"
            answer += f"• Columns: {num_columns}\n"
            answer += f"• Columns list: {', '.join(self.data.columns.tolist())}"
            
            return {
                'answer': answer,
                'query_type': 'metadata',
                'success': True,
                'data': {
                    'rows': num_rows,
                    'columns': num_columns,
                    'column_names': self.data.columns.tolist()
                },
                'visualization_suggestion': None
            }
    
    def _handle_top_n_query(self, question: str) -> Dict[str, Any]:
        """Handle top N / bottom N queries"""
        # Extract number (use configured default if not specified)
        numbers = re.findall(r'\d+', question)
        n = int(numbers[0]) if numbers else self.settings.default_top_n
        
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
        
        # Check if this is a categorical filter count (e.g., "how many males")
        cat_cols = self.data.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            # Check if column values appear in question
            unique_values = self.data[col].unique()
            for value in unique_values:
                if str(value).lower() in question_lower:
                    # This is a filter + count query
                    filtered_count = len(self.data[self.data[col] == value])
                    answer = f"There are **{filtered_count}** {value} in the {col} column."
                    
                    return {
                        'answer': answer,
                        'query_type': 'aggregation',
                        'success': True,
                        'data': {
                            'column': col,
                            'value': str(value),
                            'count': filtered_count
                        },
                        'visualization_suggestion': {
                            'type': 'bar_chart',
                            'x': col,
                            'y': 'count'
                        }
                    }
        
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
                for period, value in result.tail(self.settings.max_temporal_periods).items():
                    answer += f"  {period.strftime('%Y-%m')}: {value:,.2f}\n"
        else:
            # Just count by period
            result = self.data.groupby(pd.Grouper(key=date_col, freq=group_freq)).size()
            answer = f"Record count by {group_name}:\n"
            for period, count in result.tail(self.settings.max_temporal_periods).items():
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
