"""Unit tests for tool functions with mocked HTTP."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.tools import echo, news, search, weather


async def test_echo_returns_message():
    out = await echo.run(message="hello")
    assert out == {"echo": "hello"}


@respx.mock
async def test_news_top_headlines():
    respx.get("https://newsapi.org/v2/top-headlines").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "ok",
                "totalResults": 2,
                "articles": [
                    {
                        "title": "Big AI thing",
                        "source": {"name": "Verge"},
                        "url": "https://verge.com/x",
                        "publishedAt": "2026-05-18T12:00:00Z",
                        "description": "An AI thing.",
                    },
                    {
                        "title": "Other AI thing",
                        "source": {"name": "TechCrunch"},
                        "url": "https://tc.com/y",
                        "publishedAt": "2026-05-18T11:00:00Z",
                        "description": "Another thing.",
                    },
                ],
            },
        )
    )

    out = await news.run(category="technology", limit=2)
    assert "articles" in out
    assert len(out["articles"]) == 2
    assert out["articles"][0]["source"] == "Verge"


@respx.mock
async def test_news_topic_search():
    route = respx.get("https://newsapi.org/v2/everything").mock(
        return_value=httpx.Response(
            200, json={"status": "ok", "totalResults": 0, "articles": []}
        )
    )
    out = await news.run(topic="OpenAI")
    assert route.called
    assert out["articles"] == []


@respx.mock
async def test_news_api_error_surfaces():
    respx.get("https://newsapi.org/v2/top-headlines").mock(
        return_value=httpx.Response(429, text="rate limited")
    )
    out = await news.run()
    assert "error" in out
    assert "429" in out["error"]


@respx.mock
async def test_weather_ok():
    respx.get("https://api.openweathermap.org/data/2.5/weather").mock(
        return_value=httpx.Response(
            200,
            json={
                "name": "Bengaluru",
                "sys": {"country": "IN"},
                "main": {"temp": 27.5, "feels_like": 28.0, "humidity": 60},
                "wind": {"speed": 3.2},
                "weather": [{"description": "few clouds"}],
            },
        )
    )
    out = await weather.run(city="Bengaluru,IN")
    assert out["city"] == "Bengaluru"
    assert out["temperature"] == 27.5
    assert out["temperature_unit"] == "C"


@respx.mock
async def test_weather_city_not_found():
    respx.get("https://api.openweathermap.org/data/2.5/weather").mock(
        return_value=httpx.Response(404, text="not found")
    )
    out = await weather.run(city="Zzzzz")
    assert "error" in out


@respx.mock
async def test_search_ok():
    respx.get("https://api.search.brave.com/res/v1/web/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "web": {
                    "results": [
                        {
                            "title": "Result A",
                            "url": "https://a.example",
                            "description": "desc a",
                            "age": "1h",
                        }
                    ]
                }
            },
        )
    )
    out = await search.run(query="latest AI news", limit=1)
    assert len(out["results"]) == 1
    assert out["results"][0]["url"] == "https://a.example"


async def test_unknown_tool_invoke():
    from app.tools import registry

    out = await registry.invoke("not_a_tool", {})
    assert "error" in out
    assert "unknown tool" in out["error"]


@pytest.mark.parametrize(
    "tool_module", [news, weather, search]
)
def test_tool_schema_shape(tool_module):
    s = tool_module.TOOL_SCHEMA
    assert s["type"] == "function"
    fn = s["function"]
    assert fn["name"] == tool_module.NAME
    assert "description" in fn
    assert fn["parameters"]["type"] == "object"
