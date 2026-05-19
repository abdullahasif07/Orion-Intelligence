"""`tools` query resolver — lists registered agent tools."""

from __future__ import annotations

from app.tools import registry


def tools() -> list[str]:
    """Return the names of all tools currently registered with the agent."""
    return registry.tool_names()
