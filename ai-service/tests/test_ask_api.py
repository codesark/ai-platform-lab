"""End-to-end API tests for /ask using the offline `local` provider.

No DB and no API key required: the DB lifecycle is stubbed, retrieval is faked,
and generation/embeddings use the deterministic local provider.
"""

import os

os.environ["INFERENCE_PROVIDER"] = "local"  # before importing the app

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from agent.tools.retrieve import RetrievedChunk  # noqa: E402

API_KEY = "change-me-local-dev-key"  # matches the Settings default


@pytest.fixture
def client(monkeypatch):
    async def _noop() -> None:
        return None

    # No real DB in these tests.
    monkeypatch.setattr(main, "init_pool", _noop)
    monkeypatch.setattr(main, "close_pool", _noop)

    async def fake_retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                doc_id="faq-cancel",
                chunk_id=0,
                source="vihi-faq",
                score=0.99,
                text="You can cancel for free up to 4 hours before the scheduled start time.",
            )
        ]

    monkeypatch.setattr("rag.pipeline.retrieve_docs", fake_retrieve)

    with TestClient(main.app) as test_client:
        yield test_client


def test_healthz_is_open(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ask_requires_api_key(client):
    resp = client.post("/ask", json={"question": "what is the cancellation policy?"})
    assert resp.status_code == 401


def test_ask_rejects_empty_question(client):
    resp = client.post("/ask", json={"question": ""}, headers={"X-API-Key": API_KEY})
    assert resp.status_code == 422


def test_ask_returns_grounded_answer_with_citations(client):
    resp = client.post(
        "/ask",
        json={"question": "what is the cancellation policy?"},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert len(body["citations"]) == 1
    citation = body["citations"][0]
    assert citation["source"] == "vihi-faq"
    assert citation["doc_id"] == "faq-cancel"
    assert "cancel" in citation["snippet"].lower()
