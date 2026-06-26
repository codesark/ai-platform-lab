from agent.tools.retrieve import RetrievedChunk
from rag.prompt import build_grounded_prompt


def _chunk(i: int) -> RetrievedChunk:
    return RetrievedChunk(doc_id=f"d{i}", chunk_id=i, source="faq", score=0.9, text=f"text {i}")


def test_prompt_includes_context_and_citation_markers():
    prompt = build_grounded_prompt("how do I book?", [_chunk(1), _chunk(2)])
    assert "text 1" in prompt
    assert "[1]" in prompt and "[2]" in prompt
    assert "how do I book?" in prompt
    assert "cite" in prompt.lower()


def test_prompt_handles_no_context():
    prompt = build_grounded_prompt("q", [])
    assert "no relevant context" in prompt.lower()
