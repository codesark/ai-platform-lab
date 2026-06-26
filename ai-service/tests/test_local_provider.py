"""Tests for the offline `local` provider: determinism + lexical retrieval quality."""

import math

import pytest

from inference.local import LocalProvider


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


@pytest.fixture
def provider() -> LocalProvider:
    return LocalProvider()


async def test_embed_is_deterministic(provider: LocalProvider):
    assert await provider.embed("cancel my booking") == await provider.embed("cancel my booking")


async def test_embed_has_expected_dimension(provider: LocalProvider):
    assert len(await provider.embed("hello world")) == 768


async def test_lexically_similar_text_ranks_higher(provider: LocalProvider):
    query = await provider.embed("what is the cancellation policy")
    relevant = await provider.embed("You can cancel for free up to 4 hours before the start time.")
    unrelated = await provider.embed("ViHi accepts major credit and debit cards and UPI.")
    assert _cosine(query, relevant) > _cosine(query, unrelated)
