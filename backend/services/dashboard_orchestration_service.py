"""
Dashboard Orchestration Service
Generates intelligent dashboard component suggestions using Groq LLM
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)


class DashboardOrchestrationService:
    """Orchestrates dashboard creation with AI-powered component suggestions"""

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = Groq(api_key=self.groq_api_key)
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        logger.info("DashboardOrchestrationService initialized with Groq")

    def suggest_dashboard_components(
        self,
        columns: List[str],
        column_types: Dict[str, str],
        sample_data: Optional[List[Dict[str, Any]]] = None,
        max_components: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Generate dashboard component suggestions based on dataset schema
        
        Args:
            columns: List of column names
            column_types: Dict mapping column names to their data types
            sample_data: Optional sample rows for better context
            max_components: Maximum number of components to suggest
            
        Returns:
            List of component suggestions with visualization type and purpose
        """
        try:
            prompt = self._build_suggestion_prompt(
                columns, column_types, sample_data, max_components
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data visualization expert. Suggest dashboard components that provide maximum insight."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            suggestions_text = response.choices[0].message.content
            suggestions = self._parse_suggestions(suggestions_text)
            
            logger.info(f"Generated {len(suggestions)} dashboard component suggestions")
            return suggestions[:max_components]
            
        except Exception as e:
            logger.error(f"Failed to generate component suggestions: {e}")
            # Return default suggestions as fallback
            return self._get_default_suggestions(columns, column_types)

    def _build_suggestion_prompt(
        self,
        columns: List[str],
        column_types: Dict[str, str],
        sample_data: Optional[List[Dict[str, Any]]],
        max_components: int
    ) -> str:
        """Build prompt for component suggestions"""
        
        # Format column info
        column_info = "\n".join([
            f"  - {col}: {column_types.get(col, 'unknown')}"
            for col in columns
        ])
        
        # Add sample data if available
        sample_section = ""
        if sample_data and len(sample_data) > 0:
            sample_section = f"\n\nSample data (first 3 rows):\n{json.dumps(sample_data[:3], indent=2)}"
        
        prompt = f"""Analyze this dataset and suggest {max_components} dashboard visualization components.

Dataset Schema:
{column_info}{sample_section}

For each component, specify:
1. **id**: unique identifier (e.g., "revenue_trend", "top_customers")
2. **title**: descriptive title
3. **description**: brief explanation of insights shown
4. **visualizationType**: one of [metric, chart, pie, table]
5. **chartType**: if visualizationType is "chart" or "pie", specify: bar, line, scatter, histogram, pie, heatmap
6. **purpose**: what question this answers (e.g., "Show revenue trends over time")
7. **requiredColumns**: array of column names needed for this visualization
8. **aggregation**: if needed, specify aggregation (sum, avg, count, etc.)

Prioritize components that:
- Answer key business questions
- Show trends and patterns
- Highlight anomalies or insights
- Use appropriate visualization types for data types

Return ONLY a valid JSON array of component objects. Example:
[
  {{
    "id": "total_revenue_metric",
    "title": "Total Revenue",
    "description": "Sum of all revenue",
    "visualizationType": "metric",
    "purpose": "Show total revenue at a glance",
    "requiredColumns": ["revenue"],
    "aggregation": "sum"
  }},
  {{
    "id": "sales_trend",
    "title": "Sales Trend Over Time",
    "description": "Monthly sales performance",
    "visualizationType": "chart",
    "chartType": "line",
    "purpose": "Track sales performance over time",
    "requiredColumns": ["date", "sales"],
    "aggregation": "sum"
  }}
]"""
        
        return prompt

    def _parse_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured component suggestions"""
        try:
            # Try to extract JSON from response
            json_start = text.find('[')
            json_end = text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = text[json_start:json_end]
                suggestions = json.loads(json_text)
                
                # Validate and clean suggestions
                cleaned = []
                for suggestion in suggestions:
                    if isinstance(suggestion, dict) and 'id' in suggestion:
                        cleaned.append(suggestion)
                
                return cleaned
            
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse suggestions JSON: {e}")
            return []

    def _get_default_suggestions(
        self,
        columns: List[str],
        column_types: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Generate basic fallback suggestions when LLM fails"""
        suggestions = []
        
        # Find numeric and categorical columns
        numeric_cols = [col for col, dtype in column_types.items() if dtype in ['int64', 'float64', 'number']]
        categorical_cols = [col for col, dtype in column_types.items() if dtype in ['object', 'string', 'category']]
        date_cols = [col for col, dtype in column_types.items() if 'date' in dtype.lower() or 'time' in dtype.lower()]
        
        # Summary metrics
        if numeric_cols:
            suggestions.append({
                "id": "key_metrics",
                "title": "Key Metrics",
                "description": "Summary statistics of numeric columns",
                "visualizationType": "metric",
                "purpose": "Quick overview of numeric values",
                "requiredColumns": numeric_cols[:4],
                "aggregation": "sum"
            })
        
        # Trend chart if date + numeric
        if date_cols and numeric_cols:
            suggestions.append({
                "id": "trend_analysis",
                "title": f"{numeric_cols[0].title()} Trend",
                "description": f"Trend of {numeric_cols[0]} over time",
                "visualizationType": "chart",
                "chartType": "line",
                "purpose": "Show trends over time",
                "requiredColumns": [date_cols[0], numeric_cols[0]],
                "aggregation": "sum"
            })
        
        # Distribution if numeric
        if numeric_cols:
            suggestions.append({
                "id": "distribution",
                "title": f"{numeric_cols[0].title()} Distribution",
                "description": f"Distribution of {numeric_cols[0]}",
                "visualizationType": "chart",
                "chartType": "histogram",
                "purpose": "Understand value distribution",
                "requiredColumns": [numeric_cols[0]],
                "aggregation": None
            })
        
        # Category breakdown if categorical + numeric
        if categorical_cols and numeric_cols:
            suggestions.append({
                "id": "category_breakdown",
                "title": f"{numeric_cols[0].title()} by {categorical_cols[0].title()}",
                "description": f"Compare {numeric_cols[0]} across {categorical_cols[0]}",
                "visualizationType": "chart",
                "chartType": "bar",
                "purpose": "Compare values by category",
                "requiredColumns": [categorical_cols[0], numeric_cols[0]],
                "aggregation": "sum"
            })
        
        # Data table
        suggestions.append({
            "id": "data_table",
            "title": "Data Preview",
            "description": "Sample rows from dataset",
            "visualizationType": "table",
            "purpose": "View raw data",
            "requiredColumns": columns[:6],
            "aggregation": None
        })
        
        return suggestions[:6]


# Singleton instance
_orchestration_service = None

def get_orchestration_service() -> DashboardOrchestrationService:
    """Get singleton instance of dashboard orchestration service"""
    global _orchestration_service
    if _orchestration_service is None:
        _orchestration_service = DashboardOrchestrationService()
    return _orchestration_service
