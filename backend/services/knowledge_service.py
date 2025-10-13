"""Service layer wrapping Knowledge Agent functionality."""

from typing import Any, Dict, Optional, List

import pandas as pd

from agents.knowledge_agent.knowledge_agent import KnowledgeAgent
from shared.config import get_config


class KnowledgeService:
    def __init__(self) -> None:
        config = get_config()
        self._agent = KnowledgeAgent(groq_api_key=config.groq_api_key)

    def analyse(
        self,
        data: List[Dict[str, Any]],
        generate_insights: bool = True,
        generate_recommendations: bool = True,
    ) -> Dict[str, Any]:
        dataframe = pd.DataFrame(data)
        return self._agent.analyze_dataset(
            data=dataframe,
            generate_insights=generate_insights,
            generate_recommendations=generate_recommendations,
        )

    def ask(self, question: str) -> Dict[str, Any]:
        return self._agent.ask_question(question)

    def ask_visual(self, question: str, generate_chart: bool = True) -> Dict[str, Any]:
        """
        Answer question and optionally generate a relevant chart.
        Returns: {success, answer, chart: {type, title, figure}, method}
        """
        # First get the text answer
        text_result = self._agent.ask_question(question)
        
        if not text_result.get("success", False):
            return text_result
        
        # If chart generation disabled or query engine already provided data, return as-is
        if not generate_chart or not text_result.get("data"):
            return text_result
        
        # Try to generate a chart from the result data
        try:
            chart = self._generate_chart_from_query(text_result, question)
            if chart:
                text_result["chart"] = chart
        except Exception:
            pass  # Silently fail chart generation; text answer is still valid
        
        return text_result

    def _generate_chart_from_query(self, query_result: Dict[str, Any], question: str) -> Optional[Dict[str, Any]]:
        """Generate a chart from query result data if applicable."""
        import plotly.express as px
        import plotly.graph_objects as go
        
        query_type = query_result.get("query_type", "")
        data = query_result.get("data")
        
        if not data or not isinstance(data, dict):
            return None
        
        try:
            if query_type == "top_n":
                # Bar chart for top N results
                items = list(data.keys())
                values = list(data.values())
                fig = go.Figure(data=[go.Bar(x=items, y=values)])
                fig.update_layout(
                    title=f"Top Results: {question}",
                    xaxis_title="Category",
                    yaxis_title="Value",
                    template="plotly_white",
                )
                return {
                    "type": "bar",
                    "title": f"Top Results: {question}",
                    "figure": fig.to_dict(),
                }
            
            elif query_type == "aggregation":
                # Simple bar or metric card
                if len(data) == 1:
                    # Single metric - return as indicator
                    key, value = list(data.items())[0]
                    fig = go.Figure(go.Indicator(
                        mode="number",
                        value=value,
                        title={"text": key},
                    ))
                    fig.update_layout(template="plotly_white")
                    return {
                        "type": "indicator",
                        "title": question,
                        "figure": fig.to_dict(),
                    }
                else:
                    # Multiple aggregations - bar chart
                    fig = go.Figure(data=[go.Bar(x=list(data.keys()), y=list(data.values()))])
                    fig.update_layout(title=question, template="plotly_white")
                    return {
                        "type": "bar",
                        "title": question,
                        "figure": fig.to_dict(),
                    }
        except Exception:
            return None
        
        return None

    def summary(self) -> Dict[str, Any]:
        return self._agent.get_summary()


# Provide a shared singleton instance so that analysis state persists across routers
_SHARED_KNOWLEDGE_SERVICE: Optional[KnowledgeService] = None


def get_shared_service() -> KnowledgeService:
    global _SHARED_KNOWLEDGE_SERVICE
    if _SHARED_KNOWLEDGE_SERVICE is None:
        _SHARED_KNOWLEDGE_SERVICE = KnowledgeService()
    return _SHARED_KNOWLEDGE_SERVICE
