"""
Component Query Service
Generates MongoDB aggregation pipelines for dashboard components using Groq LLM
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from groq import Groq

logger = logging.getLogger(__name__)


class ComponentQueryService:
    """Generates MongoDB queries for specific dashboard components"""

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = Groq(api_key=self.groq_api_key)
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        logger.info("ComponentQueryService initialized with Groq")

    def generate_component_query(
        self,
        component: Dict[str, Any],
        columns: List[str],
        column_types: Dict[str, str],
        session_id: str,
        dataset_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Generate MongoDB aggregation pipeline for a specific component
        
        Args:
            component: Component configuration with visualization requirements
            columns: Available column names
            column_types: Column data types
            session_id: Session identifier for data isolation
            dataset_id: Dataset identifier
            
        Returns:
            MongoDB aggregation pipeline or None if generation fails
        """
        try:
            prompt = self._build_query_prompt(
                component, columns, column_types, session_id, dataset_id
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a MongoDB expert. Generate efficient aggregation pipelines for data visualization."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            pipeline_text = response.choices[0].message.content
            pipeline = self._parse_pipeline(pipeline_text)
            
            if pipeline:
                # Prepend security filters
                security_filters = [
                    {"$match": {"session_id": session_id, "dataset_id": dataset_id}}
                ]
                final_pipeline = security_filters + pipeline
                logger.info(f"Generated query for component: {component.get('id', 'unknown')}")
                return final_pipeline
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate component query: {e}")
            return self._get_fallback_query(component, session_id, dataset_id)

    def _build_query_prompt(
        self,
        component: Dict[str, Any],
        columns: List[str],
        column_types: Dict[str, str],
        session_id: str,
        dataset_id: str
    ) -> str:
        """Build prompt for query generation"""
        
        viz_type = component.get('visualizationType', 'chart')
        chart_type = component.get('chartType', '')
        required_cols = component.get('requiredColumns', [])
        aggregation = component.get('aggregation', '')
        purpose = component.get('purpose', '')
        
        # Format column info for required columns only
        column_info = "\n".join([
            f"  - {col}: {column_types.get(col, 'unknown')}"
            for col in required_cols if col in columns
        ])
        
        prompt = f"""Generate a MongoDB aggregation pipeline for this visualization component.

Component Details:
- ID: {component.get('id')}
- Title: {component.get('title')}
- Purpose: {purpose}
- Visualization Type: {viz_type}
- Chart Type: {chart_type}
- Required Columns: {', '.join(required_cols)}
- Aggregation: {aggregation or 'none'}

Dataset Schema (relevant columns):
{column_info}

Requirements:
1. Data is already filtered by session_id="{session_id}" and dataset_id="{dataset_id}" (don't add these filters)
2. Return pipeline as JSON array starting with $match, $group, $project, $sort, $limit stages as needed
3. For METRIC type: aggregate to single document with computed values
4. For CHART type: return data points suitable for plotting
5. For TABLE type: return up to 100 sample documents with selected columns
6. Use proper MongoDB operators: $sum, $avg, $count, $max, $min, $push, etc.
7. Handle missing/null values gracefully
8. Limit results to reasonable amounts (max 1000 documents, max 50 categories)

For example, if showing "Total Revenue":
[
  {{"$group": {{"_id": null, "total": {{"$sum": "$revenue"}}, "avg": {{"$avg": "$revenue"}}, "count": {{"$sum": 1}}}}}},
  {{"$project": {{"_id": 0, "total": 1, "avg": 1, "count": 1}}}}
]

For time series with date and value:
[
  {{"$group": {{"_id": {{"$dateToString": {{"format": "%Y-%m-%d", "date": "$date"}}}}, "value": {{"$sum": "$amount"}}}}}},
  {{"$sort": {{"_id": 1}}}},
  {{"$limit": 365}}
]

Return ONLY the JSON array pipeline, no explanations."""
        
        return prompt

    def _parse_pipeline(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """Parse LLM response into MongoDB pipeline"""
        try:
            # Extract JSON array from response
            json_start = text.find('[')
            json_end = text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = text[json_start:json_end]
                pipeline = json.loads(json_text)
                
                if isinstance(pipeline, list):
                    return pipeline
            
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse pipeline JSON: {e}")
            return None

    def _get_fallback_query(
        self,
        component: Dict[str, Any],
        session_id: str,
        dataset_id: str
    ) -> List[Dict[str, Any]]:
        """Generate basic fallback query when LLM fails"""
        viz_type = component.get('visualizationType', 'chart')
        required_cols = component.get('requiredColumns', [])
        aggregation = component.get('aggregation', '')
        
        base_match = {"$match": {"session_id": session_id, "dataset_id": dataset_id}}
        
        if viz_type == 'metric':
            # Simple aggregation for metrics
            if aggregation == 'sum' and required_cols:
                return [
                    base_match,
                    {"$group": {
                        "_id": None,
                        **{col: {"$sum": f"${col}"} for col in required_cols}
                    }},
                    {"$project": {"_id": 0}}
                ]
            elif aggregation == 'avg' and required_cols:
                return [
                    base_match,
                    {"$group": {
                        "_id": None,
                        **{col: {"$avg": f"${col}"} for col in required_cols}
                    }},
                    {"$project": {"_id": 0}}
                ]
            else:
                return [
                    base_match,
                    {"$group": {"_id": None, "count": {"$sum": 1}}},
                    {"$project": {"_id": 0}}
                ]
        
        elif viz_type == 'table':
            # Simple projection for table view
            projection = {"_id": 0, **{col: 1 for col in required_cols}} if required_cols else {"_id": 0}
            return [
                base_match,
                {"$limit": 100},
                {"$project": projection}
            ]
        
        else:
            # Simple aggregation for charts
            if len(required_cols) >= 2:
                category_col = required_cols[0]
                value_col = required_cols[1]
                return [
                    base_match,
                    {"$group": {
                        "_id": f"${category_col}",
                        "value": {"$sum": f"${value_col}"}
                    }},
                    {"$sort": {"value": -1}},
                    {"$limit": 20},
                    {"$project": {"_id": 0, "category": "$_id", "value": 1}}
                ]
            else:
                return [base_match, {"$limit": 100}]


# Singleton instance
_query_service = None

def get_component_query_service() -> ComponentQueryService:
    """Get singleton instance of component query service"""
    global _query_service
    if _query_service is None:
        _query_service = ComponentQueryService()
    return _query_service
