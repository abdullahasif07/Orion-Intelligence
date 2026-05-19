"""REST endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agent.orchestrator import run_agent
from app.agent.schemas import AskRequest, AskResponse
from app.core.logging import get_logger
from app.tools import registry

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/tools")
async def list_tools() -> dict[str, list[str]]:
    """Return the list of registered tools (handy for debugging)."""
    return {"tools": registry.tool_names()}


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    try:
        return await run_agent(req.query)
    except RuntimeError as exc:
        # e.g. missing OPENAI_API_KEY
        raise HTTPException(status_code=500, detail=str(exc)) from exc
