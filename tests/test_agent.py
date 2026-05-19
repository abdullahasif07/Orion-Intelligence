"""End-to-end tests for the ReAct loop with a mocked OpenAI client."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.agent.orchestrator import run_agent


def _make_tool_call(call_id: str, name: str, arguments: dict):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _make_completion(*, content: str | None = None, tool_calls=None):
    msg = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice = SimpleNamespace(message=msg, finish_reason="stop")
    return SimpleNamespace(choices=[choice])


async def test_agent_returns_immediately_without_tool_calls():
    """When the model emits content with no tool_calls, the loop should exit."""
    completion = _make_completion(content="All quiet on the world front.")
    with patch("app.agent.orchestrator.llm.chat", new=AsyncMock(return_value=completion)):
        resp = await run_agent("anything happening?")
    assert resp.answer == "All quiet on the world front."
    assert resp.iterations == 1
    assert resp.trace == []
    assert resp.truncated is False


async def test_agent_executes_tool_then_returns_final():
    """Iteration 1 asks for a tool; iteration 2 produces the final answer."""
    iter1 = _make_completion(
        tool_calls=[_make_tool_call("c1", "echo", {"message": "ping"})]
    )
    iter2 = _make_completion(content="Done: ping.")

    chat = AsyncMock(side_effect=[iter1, iter2])
    with patch("app.agent.orchestrator.llm.chat", new=chat):
        resp = await run_agent("please echo ping")

    assert resp.iterations == 2
    assert resp.answer == "Done: ping."
    assert len(resp.trace) == 1
    t = resp.trace[0]
    assert t.tool == "echo"
    assert t.args == {"message": "ping"}
    assert t.error is None
    assert "ping" in t.result_preview


async def test_agent_handles_parallel_tool_calls_in_one_turn():
    iter1 = _make_completion(
        tool_calls=[
            _make_tool_call("a", "echo", {"message": "one"}),
            _make_tool_call("b", "echo", {"message": "two"}),
        ]
    )
    iter2 = _make_completion(content="one and two.")
    chat = AsyncMock(side_effect=[iter1, iter2])
    with patch("app.agent.orchestrator.llm.chat", new=chat):
        resp = await run_agent("echo two things")
    assert len(resp.trace) == 2
    assert {t.args["message"] for t in resp.trace} == {"one", "two"}


async def test_agent_records_error_for_unknown_tool():
    iter1 = _make_completion(
        tool_calls=[_make_tool_call("c1", "nope", {})]
    )
    iter2 = _make_completion(content="couldn't do it.")
    chat = AsyncMock(side_effect=[iter1, iter2])
    with patch("app.agent.orchestrator.llm.chat", new=chat):
        resp = await run_agent("trigger unknown tool")
    assert resp.trace[0].tool == "nope"
    assert resp.trace[0].error and "unknown tool" in resp.trace[0].error


async def test_agent_truncates_at_max_iterations(monkeypatch):
    """If the model keeps requesting tool calls, we cap and force a final answer."""
    from app.config import settings

    monkeypatch.setattr(settings, "max_agent_iterations", 2)

    looping = _make_completion(
        tool_calls=[_make_tool_call("c1", "echo", {"message": "loop"})]
    )
    forced_final = _make_completion(content="(forced final)")

    chat = AsyncMock(side_effect=[looping, looping, forced_final])
    with patch("app.agent.orchestrator.llm.chat", new=chat):
        resp = await run_agent("keep calling")

    assert resp.truncated is True
    assert resp.iterations == 2
    assert resp.answer == "(forced final)"
    assert len(resp.trace) == 2


@pytest.mark.parametrize("bad_args", ['not json', '{"unterminated":', '{}'])
async def test_agent_handles_bad_tool_arguments(bad_args):
    """LLM occasionally emits malformed JSON or missing required args — must not crash."""
    iter1 = _make_completion(
        tool_calls=[SimpleNamespace(
            id="c1",
            type="function",
            function=SimpleNamespace(name="echo", arguments=bad_args),
        )]
    )
    iter2 = _make_completion(content="recovered")
    chat = AsyncMock(side_effect=[iter1, iter2])
    with patch("app.agent.orchestrator.llm.chat", new=chat):
        resp = await run_agent("bad args")
    assert resp.answer == "recovered"
    # All cases should record an error in the trace and the loop should still return.
    assert resp.trace[0].error is not None
