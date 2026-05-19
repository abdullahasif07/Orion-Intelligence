"""A trivial echo tool used to smoke-test the ReAct loop without external APIs.

The LLM will essentially never want to call this in production-style queries,
but it is invaluable for verifying that registration, dispatch, and trace
capture all work before any real API keys are wired up.
"""

from __future__ import annotations

from typing import Any

NAME = "echo"

TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": NAME,
        "description": (
            "Diagnostic tool. Echoes the provided message back. Only use this "
            "when explicitly asked to test the agent."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The text to echo back.",
                }
            },
            "required": ["message"],
            "additionalProperties": False,
        },
    },
}


async def run(message: str) -> dict[str, Any]:
    return {"echo": message}
