"""Tool core — the single source of truth for the platform's tools.

Each tool is a plain, frontend-agnostic function. It gets two frontends:
  - native function-calling for the agent
  - an MCP server
Keep these pure — no FastAPI, no MCP imports here.
"""

from .retrieve import RetrievedChunk, retrieve_docs

__all__ = ["RetrievedChunk", "retrieve_docs"]
