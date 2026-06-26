"""Async Postgres connection pool with pgvector support.

Degrades gracefully: if the DB is unreachable at startup the service still boots
(so /healthz stays green for liveness); /ask returns 503 until the DB is ready.
"""

from __future__ import annotations

import asyncpg
import structlog
from pgvector.asyncpg import register_vector

from config import get_settings

log = structlog.get_logger()

_pool: asyncpg.Pool | None = None


async def _init_conn(conn: asyncpg.Connection) -> None:
    await register_vector(conn)


async def init_pool() -> None:
    global _pool
    if _pool is not None:
        return
    try:
        _pool = await asyncpg.create_pool(
            get_settings().database_url, min_size=1, max_size=10, init=_init_conn
        )
        log.info("db.pool.ready")
    except Exception as exc:  # noqa: BLE001 - degrade gracefully
        log.error("db.pool.init_failed", error=str(exc))
        _pool = None


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("database is not available")
    return _pool


async def ping() -> bool:
    if _pool is None:
        return False
    try:
        async with _pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False
