# Corpus provenance

`faq.jsonl` is a **synthetic, public-safe** dataset created for this project. It models a
fictional "ViHi" local-services FAQ (bookings, cancellations, payments, etc.).

- **Source:** hand-authored / generated for the repo. Not scraped from any real product.
- **PII:** none. No real names, addresses, accounts, or customer data.
- **License:** released under the repo's MIT license.

It exists only to make the RAG pipeline demonstrable end to end. Swap in your own public-safe
corpus by replacing this file (keep the `{id, source, question, answer}` shape) and re-running
`make ingest`.
