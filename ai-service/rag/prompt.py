"""Grounded prompt construction with inline citation instructions."""

from __future__ import annotations

from agent.tools.retrieve import RetrievedChunk


def build_grounded_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    if chunks:
        context = "\n\n".join(
            f"[{i}] (source: {c.source})\n{c.text}" for i, c in enumerate(chunks, start=1)
        )
    else:
        context = "(no relevant context found)"
    return (
        "You are a helpful assistant for the ViHi local-services platform. "
        "Answer the question using ONLY the context below. Cite the sources you use "
        "inline as [n]. If the context does not contain the answer, say you don't know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )
