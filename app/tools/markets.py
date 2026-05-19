"""``get_market_snapshot`` — index / ticker snapshot via yfinance."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

NAME = "get_market_snapshot"

_DEFAULT_TICKERS = ["^GSPC", "^IXIC", "^DJI"]  # S&P 500, Nasdaq, Dow

TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": NAME,
        "description": (
            "Get a snapshot of stock / index prices. Pass a list of Yahoo Finance "
            "tickers (e.g. ['AAPL', 'MSFT', '^GSPC']). If omitted, returns the "
            "three major US indices (S&P 500, Nasdaq, Dow)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of Yahoo Finance ticker symbols.",
                    "maxItems": 10,
                }
            },
            "additionalProperties": False,
        },
    },
}


def _fetch_sync(tickers: list[str]) -> list[dict[str, Any]]:
    # Imported lazily so unit tests that don't touch this tool don't pay the
    # yfinance import cost.
    import yfinance as yf

    out: list[dict[str, Any]] = []
    for sym in tickers:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2d", interval="1d", auto_adjust=False)
            if hist.empty:
                out.append({"symbol": sym, "error": "no data"})
                continue
            last = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else last
            close = float(last["Close"])
            prev_close = float(prev["Close"])
            change = close - prev_close
            pct = (change / prev_close * 100.0) if prev_close else 0.0
            out.append(
                {
                    "symbol": sym,
                    "price": round(close, 4),
                    "previous_close": round(prev_close, 4),
                    "change": round(change, 4),
                    "change_pct": round(pct, 3),
                    "currency": getattr(ticker, "fast_info", {}).get("currency")
                    if hasattr(ticker, "fast_info")
                    else None,
                }
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("yfinance failed for %s: %s", sym, exc)
            out.append({"symbol": sym, "error": str(exc)})
    return out


async def run(tickers: list[str] | None = None) -> dict[str, Any]:
    selected = [t.strip().upper() for t in (tickers or _DEFAULT_TICKERS) if t and t.strip()]
    if not selected:
        selected = list(_DEFAULT_TICKERS)
    selected = selected[:10]

    quotes = await asyncio.to_thread(_fetch_sync, selected)
    return {"tickers": selected, "quotes": quotes}
