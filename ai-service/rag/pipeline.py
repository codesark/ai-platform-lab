"""RAG pipeline: retrieve (via the tool core) -> ground -> generate -> cite."""

from __future__ import annotations

from agent.tools.retrieve import retrieve_docs
from inference import generate
from models import Citation
from observability.tracing import observe
from rag.prompt import build_grounded_prompt


@observe(name="rag.answer")
async def answer_question(question: str, top_k: int) -> tuple[str, list[Citation]]:
    chunks = await retrieve_docs(question, top_k)
    prompt = build_grounded_prompt(question, chunks)
    text = await generate(prompt)
    citations = [
        Citation(
            doc_id=c.doc_id,
            chunk_id=c.chunk_id,
            source=c.source,
            score=round(c.score, 4),
            snippet=c.text[:200],
        )
        for c in chunks
    ]
    return text, citations
