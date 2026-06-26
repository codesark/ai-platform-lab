"""Gemini provider (hosted inference) via the google-genai SDK."""

from __future__ import annotations

from google import genai
from google.genai import types

from config import get_settings

from .base import InferenceProvider


class GeminiProvider(InferenceProvider):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model
        self._embed_model = settings.embedding_model

    async def embed(self, text: str) -> list[float]:
        resp = await self._client.aio.models.embed_content(model=self._embed_model, contents=text)
        embeddings = resp.embeddings
        if not embeddings or embeddings[0].values is None:
            raise RuntimeError("Gemini returned no embedding")
        return list(embeddings[0].values)

    async def generate(
        self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 1024
    ) -> str:
        resp = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature, max_output_tokens=max_tokens
            ),
        )
        return resp.text or ""
