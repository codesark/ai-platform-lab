# Devlog 0000 — Kickoff

Starting **ai-platform-lab**: a production-shaped reference AI platform focused on the operations
layer around LLMs — retrieval-augmented generation, evaluation and tracing, pluggable hosted and
self-hosted inference, and a tool-calling agent whose tools are exposed over MCP.

The premise: the interesting, durable engineering is the platform *around* the model — retrieval,
quality gates, observability, serving, and safe tool use — not the model itself.

First milestone: a grounded `/ask` endpoint that returns answers with citations, on a clean,
secure repo. More to follow.
