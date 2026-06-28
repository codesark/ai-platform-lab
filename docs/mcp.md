# MCP server

The platform's tools live in **one tool core**, exposed two ways: natively to the service, and over
an **MCP server** so any MCP host (Claude Desktop, Cursor, the MCP Inspector) can use them. Same code
path, two frontends — no second implementation to drift.

```
                          ┌──────────────────────────────┐
   /ask (HTTP) ──────────►│        TOOL CORE             │
                          │   retrieve_docs(query, k)    │──► embed ──► pgvector
   MCP host ──(stdio)────►│   (single source of truth)   │
   (Claude Desktop,       └──────────────────────────────┘
    Cursor, Inspector)
```

## Current surface

- **Tool:** `retrieve_docs(query, top_k=5)` — embeds the query, runs cosine ANN search over the
  corpus in pgvector, and returns the top chunks as `{doc_id, chunk_id, source, score, text}`.
  `top_k` is clamped to 1–20 and an empty query is rejected — the MCP path reuses the same validation
  as everything else, it is not a looser way in.
- **Transport:** `stdio`.

> Planned next: more tools (`lookup`, `compute`), corpus **resources** (`corpus://doc/{id}`), an
> answer-with-citations **prompt**, and a remote authenticated HTTP transport.

## Running it

The server talks to the same Postgres + pgvector as the service, so bring the database up and ingest
the corpus first:

```bash
docker compose up -d db          # Postgres + pgvector
make ingest                      # embed the corpus (needs a provider; or INFERENCE_PROVIDER=local)
make mcp                         # run the MCP server over stdio
```

Logs go to **stderr** — stdout is the JSON-RPC channel and is kept clean.

## Connecting a host

### MCP Inspector (quickest check)

```bash
npx @modelcontextprotocol/inspector \
  python -m mcp_server.server          # run from the ai-service/ directory
```

Then call `retrieve_docs` with e.g. `{"query": "what is the cancellation policy?", "top_k": 3}`.

### Claude Desktop

Add the server to `claude_desktop_config.json` (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "ai-platform-lab": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/ai-platform-lab/ai-service",
      "env": { "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/ai_platform" }
    }
  }
}
```

Restart Claude Desktop; the `retrieve_docs` tool appears and runs against your corpus.

## Observability

When Langfuse is configured, each MCP `retrieve_docs` call is traced as an `mcp.retrieve_docs` span
with the nested `inference.embed` call underneath — the same tracing the HTTP path gets.
