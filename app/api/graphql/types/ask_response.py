"""GraphQL output type returned by the `ask` query."""

from __future__ import annotations

import strawberry

from app.api.graphql.types.tool_call_trace import ToolCallTraceGQL


@strawberry.type(description="Synthesized briefing plus debug trace from the agent loop.")
class AskResponseGQL:
    answer: str = strawberry.field(description="Final synthesized briefing.")
    trace: list[ToolCallTraceGQL] = strawberry.field(
        description="Ordered list of tool calls the agent made."
    )
    iterations: int = strawberry.field(description="Number of LLM iterations consumed.")
    latency_ms: int = strawberry.field(description="End-to-end latency, in milliseconds.")
    truncated: bool = strawberry.field(
        description="True if the loop hit `MAX_AGENT_ITERATIONS` before completing."
    )
