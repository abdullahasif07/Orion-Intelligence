"""Shared test fixtures.

We force-set fake API keys *before* the app modules are imported anywhere, so
the per-tool guards (`if not settings.X_KEY: return error`) don't short-circuit
in tests. Real network is intercepted via `respx`.
"""

from __future__ import annotations

import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("NEWSAPI_KEY", "newsapi-test")
os.environ.setdefault("OPENWEATHERMAP_API_KEY", "owm-test")
os.environ.setdefault("BRAVE_SEARCH_API_KEY", "brave-test")
os.environ.setdefault("TOOL_CACHE_TTL_SECONDS", "0")  # disable cache in tests

import pytest  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.tools import registry  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_tool_cache():
    registry.clear_cache()
    yield
    registry.clear_cache()


@pytest.fixture
def settings():
    return get_settings()
