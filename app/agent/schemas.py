"""Pydantic schemas for the agent API surface."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question to Orion")


class ToolCallTrace(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    result_preview: str = Field(
        default="",
        description="First ~500 chars of the JSON-serialized tool result, for debugging.",
    )
    duration_ms: int = 0
    error: str | None = None


class AskResponse(BaseModel):
    answer: str
    trace: list[ToolCallTrace] = Field(default_factory=list)
    iterations: int = 0
    latency_ms: int = 0
    truncated: bool = Field(
        default=False,
        description="True if the agent loop hit max_iterations before producing a final answer.",
    )
