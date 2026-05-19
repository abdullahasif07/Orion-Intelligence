"""Smoke tests for REST and GraphQL endpoints."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _completion(content: str):
    msg = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="stop")])


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "orion"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_tools_endpoint_lists_registered_tools():
    r = client.get("/tools")
    assert r.status_code == 200
    names = r.json()["tools"]
    for expected in ["echo", "get_top_news", "get_weather", "web_search", "get_market_snapshot"]:
        assert expected in names


def test_rest_ask_happy_path():
    with patch(
        "app.agent.orchestrator.llm.chat",
        new=AsyncMock(return_value=_completion("hello world.")),
    ):
        r = client.post("/ask", json={"query": "what's up?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"] == "hello world."
    assert body["iterations"] == 1
    assert body["truncated"] is False


def test_graphql_ask():
    query = """
    query {
      tools
      ask(input: { query: "what's happening?" }) {
        answer
        iterations
        truncated
        trace { tool durationMs }
      }
    }
    """
    with patch(
        "app.agent.orchestrator.llm.chat",
        new=AsyncMock(return_value=_completion("nothing major.")),
    ):
        r = client.post("/graphql", json={"query": query})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "errors" not in data, data
    payload = data["data"]
    assert payload["ask"]["answer"] == "nothing major."
    assert payload["ask"]["iterations"] == 1
    assert payload["ask"]["truncated"] is False
    assert "echo" in payload["tools"]
