"""Tests for the LLM-judge score parser (pure, offline) and the judge plumbing."""

from __future__ import annotations

import pytest

from evals.judge import answer_relevancy, faithfulness, parse_score


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0.0", 0.0),
        ("1", 1.0),
        ("0.85", 0.85),
        ("Score: 0.9", 0.9),
        ("  0.42  ", 0.42),
        ("0.7 — mostly grounded", 0.7),
        ("2.0", 1.0),  # clamped up-bound
        ("-1", 1.0),  # leading '-' ignored by regex, "1" parsed then clamped
    ],
)
def test_parse_score_extracts_and_clamps(text: str, expected: float) -> None:
    assert parse_score(text) == expected


@pytest.mark.parametrize("text", ["", "no number here", "n/a"])
def test_parse_score_returns_none_when_absent(text: str) -> None:
    assert parse_score(text) is None


@pytest.mark.asyncio
async def test_judge_metrics_use_generate_and_default_safely() -> None:
    async def good_judge(prompt: str, **kwargs: object) -> str:
        return "0.9"

    async def silent_judge(prompt: str, **kwargs: object) -> str:
        return "the answer looks fine"  # no number -> defaults to 0.0

    assert await faithfulness("ctx", "ans", good_judge) == 0.9
    assert await answer_relevancy("q?", "ans", good_judge) == 0.9
    assert await faithfulness("ctx", "ans", silent_judge) == 0.0
