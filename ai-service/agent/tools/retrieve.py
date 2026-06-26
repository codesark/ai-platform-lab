"""retrieve_docs — embed a query and return the nearest corpus chunks (cosine).

This is the tool-core seam. Retrieval logic lives here, NOT in the endpoint
handler, so the agent and the MCP server can reuse it later.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    doc_id: str
    chunk_id: int
    source: str
    score: float
    text: str


async def retrieve_docs(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    # Imported lazily to keep this module import-cheap and dependency-light.
    from db import pool
    from inference import embed

    embedding = await embed(query)
    rows = await pool().fetch(
        """
        SELECT doc_id, chunk_id, source, text,
               1 - (embedding <=> $1::vector) AS score
        FROM documents
        ORDER BY embedding <=> $1::vector
        LIMIT $2
        """,
        embedding,
        top_k,
    )
    return [
        RetrievedChunk(
            doc_id=r["doc_id"],
            chunk_id=r["chunk_id"],
            source=r["source"],
            score=float(r["score"]),
            text=r["text"],
        )
        for r in rows
    ]
