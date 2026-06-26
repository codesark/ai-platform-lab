# ai-platform-lab

> A production-shaped reference AI platform: RAG with pluggable hosted and self-hosted
> inference (Gemini and vLLM), full LLM tracing and automated evals as a CI quality gate, and
> a tool-calling agent whose tools are exposed over MCP — all on Kubernetes with Terraform,
> observability, and CI/CD, with a Go→WebAssembly web UI as its face.

**Status: early development.** A grounded RAG service with citations runs locally today;
evaluation, tracing, self-hosted inference, and a tool-calling agent are in progress.

## Architecture

```
browser ── Go→WASM web UI ──┐
                            │  REST / JSON
curl / any REST client ─────┤
                            v
                 Python AI service (FastAPI)
                  • edge middleware: API-key auth, rate-limit, logging, CORS
                  • RAG: retrieve + generate     • Agent (planned)     • Eval hooks (planned)
                            │
        ┌───────────────────┼───────────────────────┬───────────────────┐
        v                   v                       v                   v
   pgvector            Inference provider        Langfuse           Tool core
   (Postgres)          Gemini | vLLM            (traces, evals)     retrieve_docs · lookup · compute
                                                                    (native + MCP server)
```

## Quickstart (local)

```bash
make setup                  # cp .env.example .env  — then add your GEMINI_API_KEY
make up                     # docker compose: Postgres+pgvector + ai-service
make ingest                 # chunk + embed the synthetic seed corpus into pgvector
make ask Q="How do I book a home cleaning?"
```

`POST /ask` returns a grounded answer with citations. `make ingest` runs on the host and needs the
Python deps locally (`python -m venv .venv && .venv/bin/pip install -r ai-service/requirements.txt`),
since it talks to Postgres on `localhost:5432` and to the Gemini API.

The optional Go→WASM UI:

```bash
make ui                     # builds web/app.wasm (TinyGo), then serve web/ on :8080
```

## Repository layout

```
ai-service/   FastAPI service: rag/, inference/, agent/tools/ (tool core), middleware/
ingestion/    corpus loader + chunker + embedder + schema.sql
corpus/       public-safe synthetic seed dataset
web/          Go→WASM web UI (optional, non-blocking)
deploy/       k8s manifests + terraform
docs/         project documentation
```

## Documentation

- [`docs/`](docs/) — architecture and project documentation.
- [`SECURITY.md`](SECURITY.md) — security policy & secret handling.

## Security & license

No secrets are committed (`gitleaks` pre-commit + CI; `.env` gitignored). The seed corpus is
synthetic and public-safe. Licensed under the [MIT License](LICENSE).
