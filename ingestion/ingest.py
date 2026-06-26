"""Load the synthetic corpus, embed each chunk, and upsert into pgvector.

Reuses the ai-service settings + inference provider so ingestion embeddings match
what retrieval uses at query time (same model, same dimension). Run from the repo
root via `make ingest` (needs the Python deps installed locally and a running DB).
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ai-service"))

import asyncpg  # noqa: E402
from pgvector.asyncpg import register_vector  # noqa: E402

from config import get_settings  # noqa: E402
from inference import embed  # noqa: E402

CORPUS = ROOT / "corpus" / "faq.jsonl"


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        start += size - overlap
    return chunks


async def main() -> None:
    settings = get_settings()
    records = [
        json.loads(line) for line in CORPUS.read_text().splitlines() if line.strip()
    ]

    conn = await asyncpg.connect(settings.database_url)
    await register_vector(conn)
    total = 0
    try:
        for rec in records:
            body = f"Q: {rec['question']}\nA: {rec['answer']}"
            for i, chunk in enumerate(chunk_text(body)):
                vector = await embed(chunk)
                await conn.execute(
                    """
                    INSERT INTO documents (doc_id, chunk_id, source, text, embedding)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (doc_id, chunk_id)
                    DO UPDATE SET text = EXCLUDED.text, embedding = EXCLUDED.embedding
                    """,
                    rec["id"],
                    i,
                    rec.get("source", "faq"),
                    chunk,
                    vector,
                )
                total += 1
    finally:
        await conn.close()
    print(f"ingested {total} chunks from {len(records)} documents")


if __name__ == "__main__":
    asyncio.run(main())
