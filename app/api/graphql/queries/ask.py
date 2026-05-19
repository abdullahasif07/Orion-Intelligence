"""`ask` query resolver — runs the full ReAct agent loop."""

from __future__ import annotations

from app.agent.orchestrator import run_agent
from app.api.graphql.inputs import AskInput
from app.api.graphql.types import AskResponseGQL, ToolCallTraceGQL


async def ask(input: AskInput) -> AskResponseGQL:
    """Ask Orion a question. Returns the synthesized answer plus a tool-call trace."""
    result = await run_agent(input.query)
    return AskResponseGQL(
        answer=result.answer,
        trace=[
            ToolCallTraceGQL(
                tool=t.tool,
                args=t.args,
                result_preview=t.result_preview,
                duration_ms=t.duration_ms,
                error=t.error,
            )
            for t in result.trace
        ],
        iterations=result.iterations,
        latency_ms=result.latency_ms,
        truncated=result.truncated,
    )
