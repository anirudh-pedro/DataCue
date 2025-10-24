"""Service layer wrapping Knowledge Agent functionality."""

from threading import Lock
from typing import Any, Dict, Optional, List

import pandas as pd

from agents.knowledge_agent.knowledge_agent import KnowledgeAgent
from shared.config import get_config


class KnowledgeService:
    """Orchestrate per-session KnowledgeAgent instances."""

    _DEFAULT_SESSION_ID = "__global__"

    def __init__(self) -> None:
        config = get_config()
        self._groq_api_key = config.groq_api_key
        self._agents: Dict[str, KnowledgeAgent] = {}
        self._lock = Lock()

    def _resolve_session_id(self, session_id: Optional[str]) -> str:
        return session_id or self._DEFAULT_SESSION_ID

    def _get_agent(self, session_key: str) -> Optional[KnowledgeAgent]:
        with self._lock:
            return self._agents.get(session_key)

    def _store_agent(self, session_key: str, agent: KnowledgeAgent) -> None:
        with self._lock:
            self._agents[session_key] = agent

    def clear_session(self, session_id: Optional[str]) -> None:
        session_key = self._resolve_session_id(session_id)
        with self._lock:
            self._agents.pop(session_key, None)

    def analyse(
        self,
        data: List[Dict[str, Any]],
        generate_insights: bool = True,
        generate_recommendations: bool = True,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        session_key = self._resolve_session_id(session_id)
        dataframe = pd.DataFrame(data)

        agent = KnowledgeAgent(groq_api_key=self._groq_api_key)
        result = agent.analyze_dataset(
            data=dataframe,
            generate_insights=generate_insights,
            generate_recommendations=generate_recommendations,
        )
        self._store_agent(session_key, agent)
        return result

    def ask(self, question: str, session_id: Optional[str] = None, *, use_cache: bool = True) -> Dict[str, Any]:
        session_key = self._resolve_session_id(session_id)
        agent = self._get_agent(session_key)
        if agent is None:
            return {
                "success": False,
                "error": "No analysis found for this session. Please upload a dataset first.",
            }
        return agent.ask_question(question, use_cache=use_cache)

    def ask_visual(
        self,
        question: str,
        session_id: Optional[str] = None,
        *,
        generate_chart: bool = True,
    ) -> Dict[str, Any]:
        """
        Answer question and optionally generate a relevant chart for the given session.
        Returns: {success, answer, chart: {type, title, figure}, method}
        """
        session_key = self._resolve_session_id(session_id)
        agent = self._get_agent(session_key)
        if agent is None:
            return {
                "success": False,
                "error": "No analysis found for this session. Please upload a dataset first.",
            }

        text_result = agent.ask_question(question)

        if not text_result.get("success", False):
            return text_result

        if not generate_chart or not text_result.get("data"):
            return text_result

        try:
            chart = self._generate_chart_from_query(text_result, question)
            if chart:
                text_result["chart"] = chart
        except Exception:
            # Chart generation is best-effort; fall back to text only.
            pass

        return text_result

    def _generate_chart_from_query(self, query_result: Dict[str, Any], question: str) -> Optional[Dict[str, Any]]:
        """Generate a chart from query result data if applicable."""
        import plotly.graph_objects as go

        query_type = query_result.get("query_type", "")
        data = query_result.get("data")

        if not data or not isinstance(data, dict):
            return None

        try:
            if query_type == "top_n":
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

            if query_type == "aggregation":
                if len(data) == 1:
                    key, value = list(data.items())[0]
                    fig = go.Figure(go.Indicator(mode="number", value=value, title={"text": key}))
                    fig.update_layout(template="plotly_white")
                    return {
                        "type": "indicator",
                        "title": question,
                        "figure": fig.to_dict(),
                    }

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

    def summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        session_key = self._resolve_session_id(session_id)
        agent = self._get_agent(session_key)
        if agent is None:
            return {"error": "No analysis found for this session."}
        return agent.get_summary()


# Provide a shared singleton instance so that analysis state persists across routers
_SHARED_KNOWLEDGE_SERVICE: Optional[KnowledgeService] = None


def get_shared_service() -> KnowledgeService:
    global _SHARED_KNOWLEDGE_SERVICE
    if _SHARED_KNOWLEDGE_SERVICE is None:
        _SHARED_KNOWLEDGE_SERVICE = KnowledgeService()
    return _SHARED_KNOWLEDGE_SERVICE
