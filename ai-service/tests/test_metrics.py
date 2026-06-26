import pytest

from evals.metrics import hit_at_k, precision_at_k, recall_at_k, reciprocal_rank


def test_hit_at_k():
    assert hit_at_k(["a"], ["x", "a", "y"], 3) == 1.0
    assert hit_at_k(["a"], ["x", "y", "z"], 3) == 0.0
    assert hit_at_k(["a"], ["x", "y", "a"], 2) == 0.0  # 'a' is at rank 3, beyond k=2


def test_recall_at_k():
    assert recall_at_k(["a", "b"], ["a", "x", "y"], 3) == 0.5
    assert recall_at_k(["a", "b"], ["a", "b", "c"], 3) == 1.0
    assert recall_at_k([], ["a"], 3) == 0.0


def test_precision_at_k():
    assert precision_at_k(["a"], ["a", "x", "y"], 3) == pytest.approx(1 / 3)
    assert precision_at_k(["a", "b"], ["a", "b", "c"], 3) == pytest.approx(2 / 3)
    assert precision_at_k(["a"], ["a"], 0) == 0.0


def test_reciprocal_rank():
    assert reciprocal_rank(["a"], ["x", "a", "y"]) == 0.5
    assert reciprocal_rank(["a"], ["x", "y", "z"]) == 0.0
