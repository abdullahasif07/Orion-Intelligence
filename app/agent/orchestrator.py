"""The ReAct loop that drives Orion.

Flow:
    1. Send (system + user) messages with all tool schemas.
    2. If the LLM returns a final text message (no tool_calls), return it.
    3. Otherwise, execute each requested tool, append results, and loop.
    4. Bail with a `truncated=True` response if we hit `max_agent_iterations`.
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.schemas import AskResponse, ToolCallTrace
from app.config import settings
from app.core import llm
from app.core.logging import get_logger
from app.tools import registry

logger = get_logger(__name__)


def _preview(obj: Any, limit: int = 500) -> str:
    try:
        s = json.dumps(obj, default=str, ensure_ascii=False)
    except Exception:
        s = str(obj)
    return s if len(s) <= limit else s[:limit] + "..."


async def run_agent(query: str) -> AskResponse:
    """Run the ReAct loop for a single user query."""
    started = time.monotonic()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    trace: list[ToolCallTrace] = []
    iterations = 0
    max_iter = settings.max_agent_iterations

    for i in range(max_iter):
        iterations = i + 1
        logger.info("agent iter %d/%d", iterations, max_iter)

        completion = await llm.chat(messages, tools=registry.openai_schemas())
        choice = completion.choices[0]
        msg = choice.message

        # No tool calls => final answer.
        if not msg.tool_calls:
            answer = msg.content or ""
            return AskResponse(
                answer=answer,
                trace=trace,
                iterations=iterations,
                latency_ms=int((time.monotonic() - started) * 1000),
                truncated=False,
            )

        # Append the assistant's tool-call message verbatim.
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        # Execute each tool call and append its result.
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError as exc:
                args = {}
                result: dict[str, Any] = {
                    "error": f"could not parse tool arguments: {exc}",
                    "raw": tc.function.arguments,
                }
                duration_ms = 0
                error_str: str | None = result["error"]
            else:
                t0 = time.monotonic()
                result = await registry.invoke(name, args)
                duration_ms = int((time.monotonic() - t0) * 1000)
                error_str = result.get("error") if isinstance(result, dict) else None

            trace.append(
                ToolCallTrace(
                    tool=name,
                    args=args,
                    result_preview=_preview(result),
                    duration_ms=duration_ms,
                    error=error_str,
                )
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str, ensure_ascii=False),
                }
            )

    # Loop exhausted without a final answer — ask the model once more, no tools.
    logger.warning("agent hit max_iterations=%d, forcing final answer", max_iter)
    messages.append(
        {
            "role": "system",
            "content": (
                "You have reached the maximum number of tool calls. Produce your "
                "best briefing now using only the information already gathered."
            ),
        }
    )
    completion = await llm.chat(messages, tools=None)
    answer = (completion.choices[0].message.content or "").strip()

    return AskResponse(
        answer=answer or "(no final answer produced)",
        trace=trace,
        iterations=iterations,
        latency_ms=int((time.monotonic() - started) * 1000),
        truncated=True,
    )
