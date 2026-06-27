# Engineering learnings

Durable technical lessons from building this platform — the design patterns that paid off and the
sharp edges worth writing down. Grows as the project does.

## Design patterns that paid off

### Offline determinism as a first-class mode

A `local` inference provider produces **deterministic** embeddings (a stable hashing bag-of-words,
L2-normalized for real lexical similarity) and a templated, clearly-marked answer. This one decision
unlocked a lot:

- the whole RAG pipeline runs with **no API key and no database**, so contributors can clone and run;
- tests are deterministic and free;
- CI runs the eval gate offline.

The lesson: make "runs with nothing configured" a real, supported path, not an afterthought. It keeps
the project approachable and the feedback loop fast.

### One inference interface, swappable providers

Everything goes through a single `InferenceProvider` (`embed` / `generate`); implementations
(hosted, self-hosted, offline) are selected by an env var and imported lazily, so the offline path
never imports a hosted SDK. Client code (retrieval, the pipeline, evals, the judge) is written once
against the interface and runs against any backend by flipping one variable.

### A retrieval "tool core" as the single source of truth

Retrieval is a small, dependency-light function returning typed chunks. The RAG pipeline calls it,
and it's the same unit that will later be exposed to a tool-calling agent and over MCP — one
implementation, many consumers, instead of three copies that drift.

### Storage-independent evals

The eval harness builds an **in-memory** index from the corpus using the same embeddings as
production, so the quality gate needs no Postgres and no secrets. That's what lets it run on every
push. See [`evals.md`](evals.md).

### Tracing that no-ops cleanly

Observability is a decorator (`@observe`) that records a span when a tracing backend is configured
and is a transparent pass-through otherwise. The service and tests run identically with or without
tracing keys — instrumentation never becomes a hard dependency. A request produces a `rag.answer`
trace with nested `inference.embed` and `inference.generate` spans.

### Grounded answers with citations

The model is prompted to answer **only** from retrieved context and to cite inline with `[n]` markers
that map back to source chunks. Grounding plus citations is what turns "a chatbot" into something you
can audit — and it's exactly what the faithfulness metric checks.

## Security baseline (from day one, not bolted on)

- Secrets never committed: `.env` is gitignored, only `.env.example` is tracked, and **gitleaks**
  runs in pre-commit and CI.
- Constant-time API-key comparison; CORS locked to the UI origin; an in-memory token-bucket rate
  limit; non-root multi-stage container image.
- Supply chain: Dependabot + `pip-audit` in CI.

## Sharp edges worth remembering

### Hosted embedding models change under you

`text-embedding-004` was retired and started returning `404 NOT_FOUND` for `embedContent`; the
current model is `gemini-embedding-001`. Two follow-on gotchas:

- it defaults to **3072** dimensions, so you must request the output dimensionality explicitly to
  match your vector column (here `VECTOR(768)`);
- embeddings produced at a non-default dimensionality aren't pre-normalized — fine for cosine
  ranking (which normalizes), but worth knowing if you compare raw distances.

Lesson: pin the embedding model *and* its dimension, and treat a model swap as a re-ingest — vectors
from two different models live in different spaces and can't be compared.

### Tracing SDKs read the process environment, not your settings

The tracing SDK auto-configures from real environment variables, but app config is loaded from
`.env` into a settings object — those are not the same thing. Loading `.env` does **not** populate
the SDK's expected env vars, so it silently disabled itself. Fix: pass credentials to the tracing
client **explicitly** from settings, so behavior is identical whether config came from `.env` or real
env vars.

### Reasoning models spend output budget on thinking

With a thinking-capable generation model, "thinking" tokens count against `max_output_tokens`. An
aggressively small cap (intended for a one-number judge reply) can be consumed before any visible
output, yielding an empty response. Lesson: don't over-constrain output length on reasoning models,
and make parsers fail closed when the expected token is absent.

### pgvector specifics

Cosine distance is the `<=>` operator; an HNSW index with `vector_cosine_ops` keeps nearest-neighbor
search fast as the corpus grows. The vector column dimension must match the embedding dimension
exactly, which ties back to pinning the embedding model above.
