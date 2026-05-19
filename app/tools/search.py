"""``web_search`` — Brave Search API."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

NAME = "web_search"

TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": NAME,
        "description": (
            "General-purpose web search via Brave. Use ONLY when the dedicated "
            "tools (news, weather, markets) are insufficient or the topic is niche."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


async def run(query: str, limit: int = 5) -> dict[str, Any]:
    if not settings.brave_search_api_key:
        return {"error": "BRAVE_SEARCH_API_KEY is not configured."}

    limit = max(1, min(int(limit or 5), 10))
    params = {"q": query, "count": limit}
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": settings.brave_search_api_key,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params=params,
            headers=headers,
        )

    if resp.status_code != 200:
        return {
            "error": f"Brave Search returned {resp.status_code}",
            "detail": resp.text[:300],
        }

    data = resp.json()
    results = []
    for item in ((data.get("web") or {}).get("results") or [])[:limit]:
        results.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "description": item.get("description"),
                "age": item.get("age"),
            }
        )

    return {"query": query, "results": results}
