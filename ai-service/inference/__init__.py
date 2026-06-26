"""Inference provider selection.

One interface (`InferenceProvider`), swappable implementations: Gemini today, with
a vLLM (OpenAI-compatible) provider planned behind the same interface so the same
client code runs against either by flipping INFERENCE_PROVIDER.
"""

from __future__ import annotations

from config import get_settings

from .base import InferenceProvider
from .gemini import GeminiProvider

_provider: InferenceProvider | None = None


def get_provider() -> InferenceProvider:
    global _provider
    if _provider is None:
        name = get_settings().inference_provider.lower()
        if name == "gemini":
            _provider = GeminiProvider()
        elif name == "vllm":
            from .vllm import VLLMProvider

            _provider = VLLMProvider()
        else:
            raise ValueError(f"unknown INFERENCE_PROVIDER: {name!r}")
    return _provider


async def embed(text: str) -> list[float]:
    return await get_provider().embed(text)


async def generate(prompt: str, **kwargs) -> str:
    return await get_provider().generate(prompt, **kwargs)
