"""Service layer wrapping Knowledge Agent functionality."""

from typing import Any, Dict, Optional

import pandas as pd

from agents.knowledge_agent.knowledge_agent import KnowledgeAgent
from shared.config import get_config


class KnowledgeService:
    def __init__(self) -> None:
        config = get_config()
        self._agent = KnowledgeAgent(groq_api_key=config.groq_api_key)

    def analyse(self, data: Dict[str, Any], generate_insights: bool = True, generate_recommendations: bool = True) -> Dict[str, Any]:
        dataframe = pd.DataFrame(data)
        return self._agent.analyze_dataset(
            data=dataframe,
            generate_insights=generate_insights,
            generate_recommendations=generate_recommendations,
        )

    def ask(self, question: str) -> Dict[str, Any]:
        return self._agent.ask_question(question)

    def summary(self) -> Dict[str, Any]:
        return self._agent.get_summary()
