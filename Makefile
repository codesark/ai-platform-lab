# ai-platform-lab — dev tasks
# Most targets just wrap docker compose + the ai-service / web toolchains.

API_KEY ?= change-me-local-dev-key
ASK_URL ?= http://localhost:8000/ask

.PHONY: help setup up down logs ingest ask test lint fmt ui precommit

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Create .env from .env.example (does not overwrite)
	@test -f .env || (cp .env.example .env && echo "Created .env — fill in GEMINI_API_KEY")

up: ## Build + start the local stack
	docker compose up --build

down: ## Stop the stack
	docker compose down

logs: ## Tail the ai-service logs
	docker compose logs -f ai-service

ingest: ## Load + embed the seed corpus into pgvector (run from repo root; needs local deps)
	python ingestion/ingest.py

ask: ## Ask a question (make ask Q="how do I book a cleaning?")
	curl -s -X POST $(ASK_URL) \
		-H "Content-Type: application/json" \
		-H "X-API-Key: $(API_KEY)" \
		-d '{"question": "$(Q)"}' | python3 -m json.tool

test: ## Run ai-service unit tests
	cd ai-service && pytest -q

eval: ## Run the retrieval eval suite and write a scorecard
	cd ai-service && python -m evals.run

lint: ## Lint + type-check Python
	cd ai-service && ruff check . && mypy .

fmt: ## Format Python
	cd ai-service && ruff format .

ui: ## Build the Go -> WASM web UI
	cd web && ./build.sh

precommit: ## Run all pre-commit hooks
	pre-commit run --all-files
