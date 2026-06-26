"""The inference-provider interface — the provider-swap seam."""

from __future__ import annotations

from abc import ABC, abstractmethod


class InferenceProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return the embedding vector for `text`."""

    @abstractmethod
    async def generate(
        self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 1024
    ) -> str:
        """Return the model's completion for `prompt`."""
