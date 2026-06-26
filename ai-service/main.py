"""FastAPI entrypoint: wiring, middleware, and the /ask endpoint."""

from __future__ import annotations

import contextlib

import structlog
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from db import close_pool, init_pool, ping
from logging_config import configure_logging
from middleware import RateLimitMiddleware, RequestLoggingMiddleware, require_api_key
from models import AskRequest, AskResponse
from rag.pipeline import answer_question

log = structlog.get_logger()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_pool()
    yield
    await close_pool()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ai-platform-lab", version="0.1.0", lifespan=lifespan)

    # CORS locked to the configured UI origin(s).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> dict[str, str]:
        if not await ping():
            raise HTTPException(status_code=503, detail="database not ready")
        return {"status": "ready"}

    @app.post("/ask", response_model=AskResponse, dependencies=[Depends(require_api_key)])
    async def ask(req: AskRequest) -> AskResponse:
        top_k = req.top_k or settings.retrieval_top_k
        try:
            text, citations = await answer_question(req.question, top_k)
        except RuntimeError as exc:  # DB not available yet
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return AskResponse(answer=text, citations=citations)

    return app


app = create_app()
