"""Tiny CLI for poking Orion without curl.

Usage:
    python -m app.cli "what's happening in tech today?"
    python -m app.cli --trace "weather in Bengaluru right now"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.agent.orchestrator import run_agent


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="orion", description="Ask Orion a question.")
    p.add_argument("query", nargs="+", help="The question to ask.")
    p.add_argument(
        "--trace",
        action="store_true",
        help="Print the tool-call trace alongside the answer.",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Print the full AskResponse as JSON.",
    )
    return p.parse_args(argv)


async def _run(query: str, *, show_trace: bool, as_json: bool) -> int:
    resp = await run_agent(query)
    if as_json:
        print(json.dumps(resp.model_dump(), indent=2, default=str))
        return 0

    print(resp.answer)
    print()
    print(
        f"-- {resp.iterations} iteration(s), "
        f"{len(resp.trace)} tool call(s), "
        f"{resp.latency_ms} ms"
        + (" (truncated)" if resp.truncated else "")
    )
    if show_trace and resp.trace:
        print()
        print("Trace:")
        for t in resp.trace:
            err = f" ERROR={t.error}" if t.error else ""
            print(f"  - {t.tool}({t.args}) [{t.duration_ms} ms]{err}")
            print(f"      -> {t.result_preview}")
    return 0


def main() -> None:
    args = _parse_args(sys.argv[1:])
    query = " ".join(args.query).strip()
    code = asyncio.run(_run(query, show_trace=args.trace, as_json=args.as_json))
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
