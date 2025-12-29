"""
Dashboard Agent
Takes metadata, sends to LLM for chart ideas, builds dashboard config, executes queries
"""

import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from groq import Groq

logger = logging.getLogger(__name__)


class DashboardAgent:
    """
    Generates dashboard configurations using LLM:
    1. Receives column metadata
    2. Sends to Groq LLM for chart/insight ideas
    3. Builds dashboard config JSON
    4. Executes safe queries to get chart data
    """
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def generate_dashboard(
        self, 
        metadata: Dict[str, Any],
        data: List[Dict[str, Any]],
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a dashboard configuration from metadata
        
        Args:
            metadata: Column names and data types from ingestion
            data: Dataset records
            user_prompt: Optional user guidance for dashboard
            
        Returns:
            Dashboard configuration with chart configs and data
        """
        try:
            # Step 1: Get chart ideas from LLM
            chart_ideas = self._get_chart_ideas(metadata, user_prompt)
            
            # Step 2: Build dashboard config
            dashboard_id = f"dashboard_{uuid.uuid4().hex[:8]}"
            
            dashboard_config = {
                "dashboard_id": dashboard_id,
                "title": chart_ideas.get("title", "Data Dashboard"),
                "description": chart_ideas.get("description", "Auto-generated dashboard"),
                "charts": []
            }
            
            # Step 3: Process each chart and build Plotly figures
            for chart in chart_ideas.get("charts", []):
                figure = self._build_plotly_figure(chart, data)
                if figure:
                    dashboard_config["charts"].append({
                        "id": f"chart_{uuid.uuid4().hex[:6]}",
                        "type": chart.get("chart_type", "bar"),
                        "title": chart.get("title", "Chart"),
                        "description": chart.get("description", ""),
                        "figure": figure
                    })
            
            return {
                "status": "success",
                "dashboard": dashboard_config,
                "insights": chart_ideas.get("insights", [])
            }
            
        except Exception as e:
            logger.error(f"Dashboard generation error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "dashboard": None
            }
    
    def _get_chart_ideas(self, metadata: Dict[str, Any], user_prompt: Optional[str]) -> Dict[str, Any]:
        """Get chart and insight ideas from LLM"""
        
        # Build column info
        columns_info = []
        for col in metadata.get("columns", []):
            columns_info.append(f"- {col['name']} ({col['type']})")
        
        prompt = f"""Analyze this dataset and suggest dashboard visualizations.

Dataset Info:
- Rows: {metadata.get('row_count', 'unknown')}
- Columns: {metadata.get('column_count', 'unknown')}

Columns:
{chr(10).join(columns_info)}

{f"User request: {user_prompt}" if user_prompt else ""}

Suggest 3-5 charts and 2-3 key insights to display.

Respond with ONLY valid JSON:
{{
  "title": "Dashboard Title",
  "description": "Brief description",
  "charts": [
    {{
      "chart_type": "bar|line|pie|scatter|histogram",
      "title": "Chart Title",
      "description": "What this shows",
      "x_axis": "column_name",
      "y_axis": "column_name",
      "aggregation": "sum|count|avg|min|max"
    }}
  ],
  "insights": [
    "Key insight about the data"
  ]
}}

Rules:
- Use only columns that exist in the dataset
- Choose chart types appropriate for the data types
- bar: categorical x, numeric y
- line: datetime/ordered x, numeric y
- pie: categorical with few unique values
- scatter: two numeric columns
- histogram: single numeric column distribution"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data visualization expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            logger.warning(f"LLM chart ideas failed: {e}, using fallback")
        
        # Fallback: basic charts
        return self._fallback_charts(metadata)
    
    def _fallback_charts(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic charts when LLM fails"""
        charts = []
        columns = metadata.get("columns", [])
        
        numeric_cols = [c for c in columns if c["type"] == "numeric"]
        categorical_cols = [c for c in columns if c["type"] == "categorical"]
        
        # Bar chart: first categorical vs first numeric
        if categorical_cols and numeric_cols:
            charts.append({
                "chart_type": "bar",
                "title": f"{numeric_cols[0]['name']} by {categorical_cols[0]['name']}",
                "x_axis": categorical_cols[0]["name"],
                "y_axis": numeric_cols[0]["name"],
                "aggregation": "sum"
            })
        
        # Histogram: first numeric
        if numeric_cols:
            charts.append({
                "chart_type": "histogram",
                "title": f"Distribution of {numeric_cols[0]['name']}",
                "x_axis": numeric_cols[0]["name"],
                "y_axis": None,
                "aggregation": "count"
            })
        
        return {
            "title": "Data Overview",
            "description": "Auto-generated dashboard",
            "charts": charts,
            "insights": ["Dashboard generated with basic charts"]
        }
    
    def _build_plotly_figure(self, chart: Dict[str, Any], data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Build a Plotly-compatible figure object from chart config and data"""
        import pandas as pd
        
        df = pd.DataFrame(data)
        chart_type = chart.get("chart_type", "bar")
        x_axis = chart.get("x_axis")
        y_axis = chart.get("y_axis")
        aggregation = chart.get("aggregation", "sum")
        
        # Common layout for dark theme
        base_layout = {
            "margin": {"t": 40, "r": 20, "b": 80, "l": 50},
            "paper_bgcolor": "transparent",
            "plot_bgcolor": "transparent",
            "font": {"color": "#e2e8f0"},
            "xaxis": {"gridcolor": "rgba(100, 116, 139, 0.2)"},
            "yaxis": {"gridcolor": "rgba(100, 116, 139, 0.2)"},
        }
        
        try:
            if chart_type == "histogram":
                if not x_axis or x_axis not in df.columns:
                    return None
                values = df[x_axis].dropna().tolist()
                if not values:
                    return None
                return {
                    "data": [{
                        "type": "histogram",
                        "x": values,
                        "marker": {"color": "#06b6d4", "line": {"color": "#0e7490", "width": 1}},
                    }],
                    "layout": {**base_layout, "bargap": 0.05}
                }
            
            if chart_type == "pie":
                if not x_axis or x_axis not in df.columns:
                    return None
                counts = df[x_axis].value_counts().head(10)
                if counts.empty:
                    return None
                return {
                    "data": [{
                        "type": "pie",
                        "labels": counts.index.tolist(),
                        "values": counts.values.tolist(),
                        "hole": 0.4,
                        "marker": {"line": {"color": "#0f172a", "width": 2}},
                        "textposition": "inside",
                        "textinfo": "percent",
                    }],
                    "layout": {
                        **base_layout,
                        "showlegend": True,
                        "legend": {"orientation": "h", "y": -0.1, "x": 0.5, "xanchor": "center"},
                    }
                }
            
            if chart_type == "scatter":
                if not x_axis or not y_axis or x_axis not in df.columns or y_axis not in df.columns:
                    return None
                scatter_df = df[[x_axis, y_axis]].dropna()
                if scatter_df.empty:
                    return None
                return {
                    "data": [{
                        "type": "scatter",
                        "mode": "markers",
                        "x": scatter_df[x_axis].tolist(),
                        "y": scatter_df[y_axis].tolist(),
                        "marker": {"color": "#22c55e", "size": 8, "opacity": 0.7},
                    }],
                    "layout": base_layout
                }
            
            if chart_type == "line":
                if not x_axis or not y_axis or x_axis not in df.columns or y_axis not in df.columns:
                    return None
                # Try to sort by x if it looks like a date/time
                line_df = df[[x_axis, y_axis]].dropna()
                if line_df.empty:
                    return None
                # Group and aggregate
                grouped = line_df.groupby(x_axis)[y_axis]
                if aggregation == "sum":
                    result = grouped.sum()
                elif aggregation == "avg":
                    result = grouped.mean()
                elif aggregation == "count":
                    result = grouped.count()
                else:
                    result = grouped.sum()
                result = result.reset_index()
                return {
                    "data": [{
                        "type": "scatter",
                        "mode": "lines+markers",
                        "x": result[x_axis].tolist(),
                        "y": result[y_axis].tolist(),
                        "line": {"color": "#8b5cf6", "width": 2},
                        "marker": {"color": "#a855f7", "size": 6},
                        "fill": "tozeroy",
                        "fillcolor": "rgba(139, 92, 246, 0.1)",
                    }],
                    "layout": base_layout
                }
            
            # Default: bar chart
            if not x_axis or not y_axis or x_axis not in df.columns or y_axis not in df.columns:
                return None
            
            # Group and aggregate
            grouped = df.groupby(x_axis)[y_axis]
            if aggregation == "sum":
                result = grouped.sum()
            elif aggregation == "avg":
                result = grouped.mean()
            elif aggregation == "count":
                result = grouped.count()
            elif aggregation == "min":
                result = grouped.min()
            elif aggregation == "max":
                result = grouped.max()
            else:
                result = grouped.sum()
            
            result = result.reset_index()
            if result.empty:
                return None
            
            return {
                "data": [{
                    "type": "bar",
                    "x": result[x_axis].tolist(),
                    "y": result[y_axis].tolist(),
                    "marker": {"color": "#6366f1", "line": {"color": "#818cf8", "width": 1}},
                }],
                "layout": {**base_layout, "bargap": 0.3}
            }
            
        except Exception as e:
            logger.warning(f"Failed to build Plotly figure: {e}")
            return None
