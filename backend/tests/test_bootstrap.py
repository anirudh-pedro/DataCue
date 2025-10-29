"""Minimal smoke tests ensuring key modules import and basic configuration works."""

import os
from pathlib import Path

import pytest

os.environ.setdefault("DISABLE_FIREBASE_AUTH", "true")

from agents.knowledge_agent.knowledge_agent import KnowledgeAgent
from agents.prediction_agent.api import prediction_api
from core.config import get_settings


def test_settings_loads_env():
    settings = get_settings()
    # The example .env ships with placeholder values; ensure we surface them.
    assert settings.groq_api_key is not None
    assert settings.mongo_uri is not None


def test_knowledge_agent_initialises_with_env_key():
    agent = KnowledgeAgent()
    # Insight generator should have the resolved API key (may be mock in tests).
    assert agent.insight_generator is not None
    # Groq client may be None if dependency missing; that's acceptable.


@pytest.mark.parametrize("directory", [
    Path("./data"),
    Path("./saved_models"),
])
def test_prediction_directories_created(directory):
    assert directory.exists()


def test_prediction_api_imports():
    assert prediction_api.app.title == "DataCue Prediction API"