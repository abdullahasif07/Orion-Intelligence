"""``get_top_news`` — fetches top headlines from NewsAPI.org."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

NAME = "get_top_news"

_NEWSAPI_CATEGORIES = {
    "business",
    "entertainment",
    "general",
    "health",
    "science",
    "sports",
    "technology",
}

TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": NAME,
        "description": (
            "Fetch the latest top headlines. Use this for any 'what's happening' "
            "or 'news' question. You may filter by category OR by free-text "
            "topic (not both)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": (
                        "Optional free-text topic (e.g. 'AI', 'OpenAI', 'India'). "
                        "If provided, performs a keyword news search."
                    ),
                },
                "category": {
                    "type": "string",
                    "enum": sorted(_NEWSAPI_CATEGORIES),
                    "description": (
                        "Optional headline category. Use 'general' for broad world news."
                    ),
                },
                "country": {
                    "type": "string",
                    "description": (
                        "Optional ISO-3166-1 alpha-2 country code (e.g. 'us', 'gb', 'in'). "
                        "Only used with `category`."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                },
            },
            "additionalProperties": False,
        },
    },
}


async def run(
    topic: str | None = None,
    category: str | None = None,
    country: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    if not settings.newsapi_key:
        return {"error": "NEWSAPI_KEY is not configured."}

    limit = max(1, min(int(limit or 5), 10))

    if topic:
        endpoint = "https://newsapi.org/v2/everything"
        params = {
            "q": topic,
            "pageSize": limit,
            "sortBy": "publishedAt",
            "language": "en",
        }
    else:
        endpoint = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": category or "general",
            "pageSize": limit,
        }
        if country:
            params["country"] = country.lower()

    headers = {"X-Api-Key": settings.newsapi_key}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(endpoint, params=params, headers=headers)

    if resp.status_code != 200:
        return {
            "error": f"NewsAPI returned {resp.status_code}",
            "detail": resp.text[:300],
        }

    data = resp.json()
    if data.get("status") != "ok":
        return {"error": "NewsAPI error", "detail": data.get("message", "unknown")}

    articles = []
    for art in (data.get("articles") or [])[:limit]:
        articles.append(
            {
                "title": art.get("title"),
                "source": (art.get("source") or {}).get("name"),
                "url": art.get("url"),
                "published_at": art.get("publishedAt"),
                "description": art.get("description"),
            }
        )

    return {
        "query": {"topic": topic, "category": category, "country": country},
        "total_results": data.get("totalResults", len(articles)),
        "articles": articles,
    }
