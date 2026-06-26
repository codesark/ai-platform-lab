"""vLLM (OpenAI-compatible) provider — not yet implemented.

Kept as an importable placeholder so the provider-selection seam type-checks.
This will talk to vLLM's OpenAI-compatible server (same client code as any
OpenAI-compatible endpoint, pointed at VLLM_BASE_URL).
"""

from __future__ import annotations

from .base import InferenceProvider


class VLLMProvider(InferenceProvider):
    def __init__(self) -> None:
        raise NotImplementedError("VLLMProvider is not yet implemented")

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    async def generate(
        self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 1024
    ) -> str:
        raise NotImplementedError
