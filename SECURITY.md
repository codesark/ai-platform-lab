# Security Policy

This is a public, MIT-licensed reference project. It is built with public-repo
safety as a first-class concern.

## Reporting a vulnerability

Please report security issues **privately** via GitHub:
**Security → Report a vulnerability** (private advisory) on this repository.
Do not open a public issue for a suspected vulnerability.

## How secrets are handled

- No secret is ever committed. `.env` is gitignored; only `.env.example`
  (placeholders) is tracked.
- [`gitleaks`](https://github.com/gitleaks/gitleaks) runs as a pre-commit hook
  **and** in CI, and fails closed.
- Cloud credentials use **OIDC / Workload Identity**, never long-lived JSON keys
  committed to the repo.
- Terraform state is stored in a **remote, encrypted, locked** backend and is
  never committed (`*.tfstate` is gitignored).
- API keys (Gemini, Langfuse) live only in local `.env` and in GitHub Actions
  **secrets**.

## Application security posture

- Input validation + size limits on every endpoint (Pydantic).
- API-key auth, rate-limiting, and CORS (locked to the UI origin) as FastAPI
  middleware.
- The seed corpus is **synthetic and public-safe** — no PII.
- Agent tools (planned) are allow-listed and argument-validated server-side; the
  MCP server authenticates its transport and treats tool descriptions/results as
  untrusted (tool-poisoning / prompt-injection defense).
