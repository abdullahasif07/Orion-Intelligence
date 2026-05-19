"""Thin async wrapper around the OpenAI Chat Completions API."""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """Return a lazily-instantiated singleton OpenAI client."""
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to your .env file."
            )
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def chat(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    *,
    model: str | None = None,
    temperature: float = 0.2,
) -> ChatCompletion:
    """Issue a single chat completion request.

    `messages` follows the OpenAI chat schema. `tools` is the OpenAI tool list
    (each entry having {"type": "function", "function": {...}}).
    """
    client = get_client()
    kwargs: dict[str, Any] = {
        "model": model or settings.openai_model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    logger.debug("openai.chat: model=%s, tools=%d", kwargs["model"], len(tools or []))
    return await client.chat.completions.create(**kwargs)
