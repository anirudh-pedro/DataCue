"""Service layer wrapping Knowledge Agent functionality."""

from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, Optional, List

import pandas as pd

from agents.knowledge_agent.knowledge_agent import KnowledgeAgent
from shared.config import get_config
from core.gridfs_service import get_gridfs_service


class KnowledgeService:
    """Orchestrate per-session KnowledgeAgent instances."""

    _MAX_SESSIONS = 100  # Maximum number of concurrent sessions
    _SESSION_TTL_HOURS = 24  # Sessions expire after 24 hours of inactivity

    def __init__(self) -> None:
        config = get_config()
        self._groq_api_key = config.groq_api_key
        self._agents: Dict[str, KnowledgeAgent] = {}
        self._access_times: Dict[str, datetime] = {}  # Track last access time
        self._lock = Lock()

    def _validate_session_id(self, session_id: Optional[str]) -> str:
        """Validate and return session_id, raising error if missing."""
        if not session_id:
            raise ValueError(
                "session_id is required. Please provide a valid session ID to isolate agent state."
            )
        return session_id

    def _cleanup_expired_sessions(self) -> None:
        """Remove sessions that have exceeded TTL. Must be called within lock."""
        now = datetime.now(timezone.utc)
        ttl_delta = timedelta(hours=self._SESSION_TTL_HOURS)
        expired_keys = [
            key for key, last_access in self._access_times.items()
            if now - last_access > ttl_delta
        ]
        for key in expired_keys:
            self._agents.pop(key, None)
            self._access_times.pop(key, None)

    def _evict_lru_session(self) -> None:
        """Evict the least recently used session. Must be called within lock."""
        if not self._access_times:
            return
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        self._agents.pop(lru_key, None)
        self._access_times.pop(lru_key, None)

    def _get_agent(self, session_key: str) -> Optional[KnowledgeAgent]:
        with self._lock:
            self._cleanup_expired_sessions()
            agent = self._agents.get(session_key)
            if agent:
                self._access_times[session_key] = datetime.now(timezone.utc)
            return agent

    def _store_agent(self, session_key: str, agent: KnowledgeAgent) -> None:
        with self._lock:
            self._cleanup_expired_sessions()
            
            # If at capacity, evict LRU session
            if len(self._agents) >= self._MAX_SESSIONS and session_key not in self._agents:
                self._evict_lru_session()
            
            self._agents[session_key] = agent
            self._access_times[session_key] = datetime.now(timezone.utc)

    def clear_session(self, session_id: str) -> None:
        """Clear agent state for a specific session."""
        session_key = self._validate_session_id(session_id)
        with self._lock:
            self._agents.pop(session_key, None)
            self._access_times.pop(session_key, None)

    def analyse(
        self,
        data: List[Dict[str, Any]] = None,
        gridfs_id: str = None,
        generate_insights: bool = True,
        generate_recommendations: bool = True,
        session_id: str = None,
    ) -> Dict[str, Any]:
        """Analyze dataset and store agent for the session."""
        session_key = self._validate_session_id(session_id)
        
        # Load from GridFS if ID provided, otherwise use data
        if gridfs_id:
            gridfs_service = get_gridfs_service()
            file_stream = gridfs_service.get_file_stream(gridfs_id)
            dataframe = pd.read_csv(file_stream)
        elif data:
            dataframe = pd.DataFrame(data)
        else:
            raise ValueError("Either 'data' or 'gridfs_id' must be provided")

        agent = KnowledgeAgent(groq_api_key=self._groq_api_key)
        result = agent.analyze_dataset(
            data=dataframe,
            generate_insights=generate_insights,
            generate_recommendations=generate_recommendations,
        )
        
        # Store gridfs_id in agent metadata for later use
        if gridfs_id:
            agent._gridfs_id = gridfs_id
            
        self._store_agent(session_key, agent)
        return result

    def ask(self, question: str, session_id: str = None, *, use_cache: bool = True) -> Dict[str, Any]:
        """Ask a question within a specific session context."""
        session_key = self._validate_session_id(session_id)
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
        session_id: str = None,
        *,
        generate_chart: bool = True,
    ) -> Dict[str, Any]:
        """
        Answer question and optionally generate a relevant chart for the given session.
        Returns: {success, answer, chart: {type, title, figure}, method}
        """
        session_key = self._validate_session_id(session_id)
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

    def summary(self, session_id: str = None) -> Dict[str, Any]:
        """Get summary of analysis for a specific session."""
        session_key = self._validate_session_id(session_id)
        agent = self._get_agent(session_key)
        if agent is None:
            return {"error": "No analysis found for this session."}
        return agent.get_summary()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the session cache for monitoring."""
        with self._lock:
            now = datetime.now(timezone.utc)
            return {
                "active_sessions": len(self._agents),
                "max_sessions": self._MAX_SESSIONS,
                "ttl_hours": self._SESSION_TTL_HOURS,
                "oldest_session_age_hours": (
                    (now - min(self._access_times.values())).total_seconds() / 3600
                    if self._access_times else 0
                ),
                "newest_session_age_hours": (
                    (now - max(self._access_times.values())).total_seconds() / 3600
                    if self._access_times else 0
                ),
            }


# Provide a shared singleton instance so that analysis state persists across routers
_SHARED_KNOWLEDGE_SERVICE: Optional[KnowledgeService] = None


def get_shared_service() -> KnowledgeService:
    global _SHARED_KNOWLEDGE_SERVICE
    if _SHARED_KNOWLEDGE_SERVICE is None:
        _SHARED_KNOWLEDGE_SERVICE = KnowledgeService()
    return _SHARED_KNOWLEDGE_SERVICE
