"""Retrieval evaluation metrics — pure functions over expected vs retrieved IDs."""

from __future__ import annotations

from collections.abc import Sequence


def hit_at_k(expected: Sequence[str], retrieved: Sequence[str], k: int) -> float:
    """1.0 if any expected ID appears in the top-k, else 0.0."""
    top = set(retrieved[:k])
    return 1.0 if any(e in top for e in expected) else 0.0


def recall_at_k(expected: Sequence[str], retrieved: Sequence[str], k: int) -> float:
    """Fraction of expected IDs found in the top-k."""
    gold = set(expected)
    if not gold:
        return 0.0
    top = set(retrieved[:k])
    return sum(1 for e in gold if e in top) / len(gold)


def precision_at_k(expected: Sequence[str], retrieved: Sequence[str], k: int) -> float:
    """Fraction of the top-k that are expected."""
    if k <= 0:
        return 0.0
    gold = set(expected)
    return sum(1 for r in retrieved[:k] if r in gold) / k


def reciprocal_rank(expected: Sequence[str], retrieved: Sequence[str]) -> float:
    """1 / rank of the first expected ID (0.0 if none retrieved)."""
    gold = set(expected)
    for i, r in enumerate(retrieved, start=1):
        if r in gold:
            return 1.0 / i
    return 0.0
