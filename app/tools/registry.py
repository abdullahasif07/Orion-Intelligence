"""Tool registry.

Each tool module exposes:
- ``NAME``: the canonical tool name (matches what the LLM emits).
- ``TOOL_SCHEMA``: the OpenAI function/tool schema dict.
- ``async def run(**kwargs) -> dict``: the actual implementation.

Adding a new tool is just creating a new module and registering it in
``_TOOLS`` below.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.tools import echo, markets, news, search, weather

logger = get_logger(__name__)


ToolFn = Callable[..., Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class Tool:
    name: str
    schema: dict[str, Any]
    run: ToolFn


def _build_registry() -> dict[str, Tool]:
    modules = [echo, news, weather, search, markets]
    registry: dict[str, Tool] = {}
    for mod in modules:
        registry[mod.NAME] = Tool(name=mod.NAME, schema=mod.TOOL_SCHEMA, run=mod.run)
    return registry


_TOOLS: dict[str, Tool] = _build_registry()


# ---------- public API ----------


def openai_schemas() -> list[dict[str, Any]]:
    """Return the list of tool schemas to pass to the OpenAI API."""
    return [t.schema for t in _TOOLS.values()]


def tool_names() -> list[str]:
    return list(_TOOLS.keys())


# Simple in-memory TTL cache: (tool_name, sorted-args-json) -> (expires_at, result)
_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}


def _cache_key(name: str, args: dict[str, Any]) -> tuple[str, str]:
    return (name, json.dumps(args, sort_keys=True, default=str))


async def invoke(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Invoke a registered tool by name with the given kwargs.

    Wraps the call with a timeout and a small TTL cache.
    """
    if name not in _TOOLS:
        return {"error": f"unknown tool: {name}", "available": tool_names()}

    key = _cache_key(name, args)
    now = time.monotonic()
    if settings.tool_cache_ttl_seconds > 0:
        cached = _cache.get(key)
        if cached and cached[0] > now:
            logger.debug("tool cache hit: %s", name)
            return cached[1]

    tool = _TOOLS[name]
    try:
        result = await asyncio.wait_for(
            tool.run(**args),
            timeout=settings.tool_timeout_seconds,
        )
    except TimeoutError:
        return {"error": f"tool '{name}' timed out after {settings.tool_timeout_seconds}s"}
    except TypeError as exc:
        # Bad arguments from the LLM
        return {"error": f"invalid arguments for '{name}': {exc}"}
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("tool '%s' raised", name)
        return {"error": f"tool '{name}' failed: {exc}"}

    if settings.tool_cache_ttl_seconds > 0:
        _cache[key] = (now + settings.tool_cache_ttl_seconds, result)

    return result


def clear_cache() -> None:
    """Test helper."""
    _cache.clear()
