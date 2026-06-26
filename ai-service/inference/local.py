"""Deterministic, dependency-free inference provider for local dev / CI.

No API key or network required. Embeddings are a hashing bag-of-words vector, so
cosine similarity reflects token overlap and retrieval actually returns relevant
chunks. Generation returns a templated, clearly-marked non-LLM answer that points
at the retrieved sources. Select with INFERENCE_PROVIDER=local.
"""

from __future__ import annotations

import re
import zlib

from config import get_settings

from .base import InferenceProvider

_TOKEN = re.compile(r"[a-z0-9]+")
_NO_CONTEXT = "(no relevant context found)"


class LocalProvider(InferenceProvider):
    def __init__(self) -> None:
        self._dim = get_settings().embedding_dim

    async def embed(self, text: str) -> list[float]:
        # Hashing vectorizer: stable token -> bucket via crc32 (deterministic
        # across processes, unlike hash()), then L2-normalize for cosine.
        vec = [0.0] * self._dim
        for token in _TOKEN.findall(text.lower()):
            vec[zlib.crc32(token.encode()) % self._dim] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0.0:
            vec = [v / norm for v in vec]
        return vec

    async def generate(
        self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 1024
    ) -> str:
        if _NO_CONTEXT in prompt:
            return "[local provider — no live model] I don't have relevant context to answer that."
        return (
            "[local provider — no live model] Answer assembled from the retrieved context above; "
            "see the cited sources. [1]"
        )
