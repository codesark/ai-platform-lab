"""MCP server: the retrieve_docs tool is registered, shaped, and arg-validated.

Uses FastMCP's in-process call_tool with the tool core stubbed, so no DB is needed.
"""

from __future__ import annotations

import pytest

import mcp_server.server as server
from agent.tools.retrieve import RetrievedChunk


async def test_tool_is_registered() -> None:
    tools = await server.mcp.list_tools()
    assert "retrieve_docs" in {t.name for t in tools}


async def test_call_tool_returns_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake(query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                doc_id="faq-cancel",
                chunk_id=0,
                source="corpus",
                score=0.98765,
                text="cancel policy",
            )
        ]

    monkeypatch.setattr(server, "_retrieve_docs", fake)
    result = await server.mcp.call_tool("retrieve_docs", {"query": "cancel?", "top_k": 3})
    # FastMCP wraps the return; assert the payload made it through regardless of shape.
    assert "faq-cancel" in str(result)
    assert "0.9877" in str(result)  # score rounded to 4dp


async def test_call_tool_clamps_top_k(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, int] = {}

    async def fake(query: str, top_k: int = 5) -> list[RetrievedChunk]:
        seen["top_k"] = top_k
        return []

    monkeypatch.setattr(server, "_retrieve_docs", fake)
    await server.mcp.call_tool("retrieve_docs", {"query": "x", "top_k": 999})
    assert seen["top_k"] == server.MAX_TOP_K
