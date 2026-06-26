"""Edge middleware: API-key auth, rate-limiting, request logging.

These are the cross-cutting concerns a separate gateway would have held; they
live here as FastAPI/Starlette middleware instead.
"""

from __future__ import annotations

import hmac
import time
import uuid

import structlog
from fastapi import Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import get_settings

log = structlog.get_logger()


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Constant-time API-key check. Used as a route dependency."""
    expected = get_settings().ai_service_api_key
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or missing API key"
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(
            request_id=request_id, method=request.method, path=request.url.path
        )
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info("request", status=response.status_code, duration_ms=duration_ms)
        response.headers["x-request-id"] = request_id
        structlog.contextvars.clear_contextvars()
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory token bucket per API key (or client IP).

    Single-process only — fine for local dev / one replica. Use a shared store
    (e.g. Redis) when running multiple replicas.
    """

    def __init__(self, app, capacity: int = 60, refill_per_sec: float = 1.0) -> None:
        super().__init__(app)
        self._capacity = capacity
        self._refill = refill_per_sec
        self._buckets: dict[str, tuple[float, float]] = {}

    async def dispatch(self, request: Request, call_next):
        client = request.headers.get("x-api-key") or (
            request.client.host if request.client else "anon"
        )
        now = time.monotonic()
        tokens, last = self._buckets.get(client, (float(self._capacity), now))
        tokens = min(self._capacity, tokens + (now - last) * self._refill)
        if tokens < 1.0:
            self._buckets[client] = (tokens, now)
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        self._buckets[client] = (tokens - 1.0, now)
        return await call_next(request)
