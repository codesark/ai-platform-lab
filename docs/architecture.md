# Architecture

> Early documentation — expanded as the system grows.

## Components

- **AI service (FastAPI, REST/JSON)** — RAG today; agent and eval hooks planned. Owns edge concerns
  (API-key auth, rate-limit, request logging, CORS) as middleware.
- **Tool core** (`ai-service/agent/tools/`) — `retrieve_docs` (with `lookup`, `compute` planned),
  the single source of truth, exposed natively to the agent and over an MCP server.
- **Vector store** — Postgres + pgvector (HNSW, cosine distance).
- **Inference provider** — `gemini` today; a `vllm` (OpenAI-compatible) provider planned behind the
  same interface.
- **Web UI** — Go→WebAssembly, calls the REST API (optional, non-blocking).

## Request flow (`POST /ask`)

```
client → middleware (auth, rate-limit, log, CORS)
       → retrieve_docs(query, top_k)        # embed query, pgvector ANN search
       → build_grounded_prompt(...)         # context + citation instructions
       → inference.generate(prompt)         # Gemini (or vLLM)
       → { answer, citations[] }
```
