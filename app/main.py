"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.api.graphql import graphql_router
from app.api.rest import router as rest_router
from app.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Orion",
        description="JARVIS-lite briefing agent — REST + GraphQL backend.",
        version=__version__,
    )

    app.include_router(rest_router, tags=["orion"])
    app.include_router(graphql_router, prefix="/graphql")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": "orion",
            "version": __version__,
            "docs": "/docs",
            "graphql": "/graphql",
        }

    logger.info("Orion ready (model=%s)", settings.openai_model)
    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
