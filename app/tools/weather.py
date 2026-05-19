"""``get_weather`` — current conditions via OpenWeatherMap."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

NAME = "get_weather"

TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": NAME,
        "description": (
            "Get current weather conditions for a city. Returns temperature, "
            "feels-like, conditions, humidity, and wind."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, optionally with country code, e.g. 'Bengaluru,IN' or 'San Francisco'.",
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "default": "metric",
                },
            },
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}


async def run(city: str, units: str = "metric") -> dict[str, Any]:
    if not settings.openweathermap_api_key:
        return {"error": "OPENWEATHERMAP_API_KEY is not configured."}

    if units not in {"metric", "imperial"}:
        units = "metric"

    params = {
        "q": city,
        "units": units,
        "appid": settings.openweathermap_api_key,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.openweathermap.org/data/2.5/weather", params=params
        )

    if resp.status_code == 404:
        return {"error": f"city not found: {city}"}
    if resp.status_code != 200:
        return {
            "error": f"OpenWeatherMap returned {resp.status_code}",
            "detail": resp.text[:300],
        }

    data = resp.json()
    main = data.get("main") or {}
    wind = data.get("wind") or {}
    weather_list = data.get("weather") or []
    weather0 = weather_list[0] if weather_list else {}

    temp_unit = "C" if units == "metric" else "F"
    wind_unit = "m/s" if units == "metric" else "mph"

    return {
        "city": data.get("name"),
        "country": (data.get("sys") or {}).get("country"),
        "conditions": weather0.get("description"),
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity_pct": main.get("humidity"),
        "wind_speed": wind.get("speed"),
        "temperature_unit": temp_unit,
        "wind_unit": wind_unit,
    }
