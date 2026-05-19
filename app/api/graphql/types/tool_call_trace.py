"""GraphQL output type mirroring `app.agent.schemas.ToolCallTrace`."""

from __future__ import annotations

import strawberry
from strawberry.scalars import JSON


@strawberry.type(description="A single tool invocation captured during the agent loop.")
class ToolCallTraceGQL:
    tool: str = strawberry.field(description="Registered tool name.")
    args: JSON = strawberry.field(description="Arguments the LLM passed to the tool.")
    result_preview: str = strawberry.field(
        description="First ~500 chars of the JSON-serialized tool result."
    )
    duration_ms: int = strawberry.field(description="Tool execution time, in milliseconds.")
    error: str | None = strawberry.field(
        default=None, description="Populated when the tool failed."
    )
