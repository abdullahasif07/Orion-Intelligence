# Orion

A JARVIS-lite AI agent backend. Ask it *"what's happening in the world right now?"* and it runs a tool-calling loop (OpenAI ReAct) over live data sources to return a clean, grounded briefing.

- **Stack**: FastAPI + Strawberry GraphQL + OpenAI tool-calling
- **Tools**: NewsAPI, OpenWeatherMap, Brave Search, Yahoo Finance (yfinance)
- **Scope**: backend only (frontend + voice come later)

---

## Architecture

```
  client  ─►  FastAPI  ─►  Agent Orchestrator  ─►  OpenAI Chat
                              │   ▲                    │
                              │   └────── tool_calls ──┘
                              ▼
                       Tool Registry
                       ├── get_top_news      (NewsAPI)
                       ├── get_weather       (OpenWeatherMap)
                       ├── web_search        (Brave)
                       └── get_market_snapshot (yfinance)
```

The orchestrator loops at most `MAX_AGENT_ITERATIONS` (default 5) times: model decides which tools to call → backend executes them → results fed back → model produces a final briefing.

---

## Quickstart

Using `make` (recommended):

```bash
make setup        # venv + deps + .env from template
# fill in OPENAI_API_KEY and at least NEWSAPI_KEY in .env
make dev          # http://localhost:8000  (reload on save)
```

Manual:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

Open:

- Swagger UI: <http://localhost:8000/docs>
- GraphiQL:   <http://localhost:8000/graphql>

Run `make help` to see every available target.

---

## Required environment variables

| Key | Required for | Where to get |
| --- | --- | --- |
| `OPENAI_API_KEY` | the LLM | <https://platform.openai.com> |
| `NEWSAPI_KEY` | `get_top_news` | <https://newsapi.org> (free) |
| `OPENWEATHERMAP_API_KEY` | `get_weather` | <https://openweathermap.org/api> (free) |
| `BRAVE_SEARCH_API_KEY` | `web_search` | <https://brave.com/search/api> (free) |
| (none) | `get_market_snapshot` | yfinance scrapes Yahoo, no key |

Optional knobs: `OPENAI_MODEL` (default `gpt-4o`), `MAX_AGENT_ITERATIONS`, `TOOL_TIMEOUT_SECONDS`, `TOOL_CACHE_TTL_SECONDS`.

---

## Talking to Orion

### 1. CLI (fastest dev loop)

```bash
python -m app.cli "what's happening in tech today?"
python -m app.cli --trace "weather in Bengaluru right now"
python -m app.cli --json "how are US markets doing?"
```

### 2. REST

```bash
curl -s http://localhost:8000/ask \
  -H 'content-type: application/json' \
  -d '{"query":"what is happening in tech today?"}' | jq
```

Response shape:

```json
{
  "answer": "...synthesized briefing...",
  "trace": [
    {
      "tool": "get_top_news",
      "args": {"category": "technology", "limit": 5},
      "result_preview": "{\"articles\": [...]}",
      "duration_ms": 412,
      "error": null
    }
  ],
  "iterations": 2,
  "latency_ms": 2150,
  "truncated": false
}
```

### 3. GraphQL

```graphql
query {
  ask(input: { query: "what is happening in tech today?" }) {
    answer
    iterations
    latencyMs
    truncated
    trace { tool args durationMs error }
  }
}
```

You can also list registered tools:

```graphql
query { tools }
```

---

## Example queries to try

| Query | Tool(s) the model is likely to pick |
| --- | --- |
| "what's the top tech news right now?" | `get_top_news` |
| "what's the weather in San Francisco?" | `get_weather` |
| "how did the S&P 500 close today?" | `get_market_snapshot` |
| "summary of the latest OpenAI announcement" | `get_top_news` or `web_search` |
| "give me a full world briefing" | several tools in parallel |

---

## Project layout

```
orion/
├── app/
│   ├── main.py              # FastAPI app, mounts REST + GraphQL
│   ├── config.py            # pydantic-settings
│   ├── cli.py               # `python -m app.cli "..."`
│   ├── core/
│   │   ├── llm.py           # async OpenAI wrapper
│   │   └── logging.py
│   ├── agent/
│   │   ├── orchestrator.py  # ReAct loop
│   │   ├── prompts.py       # SYSTEM_PROMPT
│   │   └── schemas.py
│   ├── tools/
│   │   ├── registry.py      # TTL cache + timeout + dispatch
│   │   ├── echo.py          # diagnostic tool
│   │   ├── news.py
│   │   ├── weather.py
│   │   ├── search.py
│   │   └── markets.py
│   └── api/
│       ├── rest.py
│       └── graphql/
│           ├── schema.py      # builds strawberry.Schema + router
│           ├── root.py        # root Query / Mutation types
│           ├── types/         # output types (1 per file)
│           ├── inputs/        # input types  (1 per file)
│           ├── queries/       # query resolvers (1 per file)
│           └── mutations/     # mutation resolvers (1 per file)
└── tests/
    ├── test_tools.py
    ├── test_agent.py
    └── test_api.py
```

---

## Adding a new tool

1. Create `app/tools/my_tool.py` exporting `NAME`, `TOOL_SCHEMA`, and `async def run(**kwargs)`.
2. Append the module to the `modules` list in `app/tools/registry.py::_build_registry`.
3. (Optional) Add tests in `tests/test_tools.py`.

That's it — the orchestrator is tool-agnostic, so the LLM will see the new tool on the next request.

---

## Running tests

```bash
.venv/bin/python -m pytest -q
```

Tests mock both `httpx` (via `respx`) and the OpenAI client, so they run fully offline and don't burn API credits.

---

## Roadmap (not in this MVP)

- Conversation memory / session ids
- Streaming responses (SSE / GraphQL subscriptions)
- Voice layer: clap detector → wake word (Porcupine) → Whisper STT → `edge-tts` / ElevenLabs TTS
- Frontend (cool UI)
