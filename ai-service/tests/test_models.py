import pytest
from pydantic import ValidationError

from models import AskRequest


def test_rejects_empty_question():
    with pytest.raises(ValidationError):
        AskRequest(question="")


def test_rejects_oversized_question():
    with pytest.raises(ValidationError):
        AskRequest(question="x" * 2001)


def test_top_k_bounds():
    with pytest.raises(ValidationError):
        AskRequest(question="ok", top_k=0)
    assert AskRequest(question="ok", top_k=5).top_k == 5
