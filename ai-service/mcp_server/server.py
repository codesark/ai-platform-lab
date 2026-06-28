"""MCP server exposing the tool core over stdio.

One tool today — `retrieve_docs` — backed by the same retrieval that powers `/ask`,
so the corpus is reachable from any MCP host (Claude Desktop, Cursor, the MCP
Inspector). The tool core stays the single source of truth; this is just a second
frontend onto it.

stdio note: stdout is the JSON-RPC channel and must stay clean, so logs are routed
to stderr. Tool args are validated here (the MCP path is not a looser way in).
"""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from agent.tools.retrieve import retrieve_docs as _retrieve_docs
from db import close_pool, init_pool
from logging_config import configure_logging
from observability.tracing import observe

MAX_TOP_K = 20


@asynccontextmanager
async def _lifespan(_server: FastMCP) -> AsyncIterator[dict[str, object]]:
    # Same Postgres + pgvector pool the HTTP service uses.
    await init_pool()
    try:
        yield {}
    finally:
        await close_pool()


mcp = FastMCP(
    "ai-platform-lab",
    instructions=(
        "Grounded retrieval over the ai-platform-lab corpus. Call retrieve_docs to "
        "fetch the most relevant chunks (with source and similarity score) for a query."
    ),
    lifespan=_lifespan,
)


@observe(name="mcp.retrieve_docs")
async def _retrieve(query: str, top_k: int) -> list[dict[str, object]]:
    chunks = await _retrieve_docs(query, top_k)
    return [
        {
            "doc_id": c.doc_id,
            "chunk_id": c.chunk_id,
            "source": c.source,
            "score": round(c.score, 4),
            "text": c.text,
        }
        for c in chunks
    ]


@mcp.tool()
async def retrieve_docs(query: str, top_k: int = 5) -> list[dict[str, object]]:
    """Search the knowledge base and return the most relevant chunks.

    Args:
        query: natural-language question or search text.
        top_k: how many chunks to return (clamped to 1-20).
    """
    if not query.strip():
        raise ValueError("query must not be empty")
    top_k = max(1, min(top_k, MAX_TOP_K))
    return await _retrieve(query, top_k)


def main() -> None:
    configure_logging(stream=sys.stderr)  # keep stdout clean for JSON-RPC
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
