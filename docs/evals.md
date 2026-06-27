# Evaluation

How this project measures RAG quality. Quality has two halves — did we retrieve the right sources,
and did the model use them well — and there's a metric layer for each:

- **Retrieval metrics** (hit@k, recall@k, precision@k, MRR) — always on, deterministic, and
  storage-independent, so they run as an offline CI gate with no API key or database.
- **LLM-judge answer metrics** (faithfulness, answer relevancy) — opt-in, since they need a real
  generative model to grade the produced answer.

Both are written to a scorecard (JSON + Markdown). The runner exits non-zero if any enabled metric
falls below its threshold, which is what makes it a gate.

## Retrieval metrics

These grade the *search* step — did we fetch the right source docs — independent of the generated
answer. They're standard information-retrieval metrics, implemented in `ai-service/evals/metrics.py`.

### Setup

Each eval example is a **question** plus the doc(s) that *should* be retrieved (`expected_doc_ids`,
the hand-labeled "gold"). We retrieve the **top-k** (k=3, because the pipeline feeds the top-3 chunks
to the model) and compare retrieved IDs to gold IDs. "**@k**" means "looking only at the top k."

| Metric | Question it answers | Formula (per query) |
|---|---|---|
| **hit@k** | Did we get *at least one* right doc in the top-k? (binary) | `1 if (gold ∩ top-k) else 0` |
| **recall@k** | Of *all* docs that should be retrieved, what fraction did we get? | `|gold ∩ top-k| / |gold|` |
| **precision@k** | Of the k we returned, what fraction were relevant? (noise) | `|gold ∩ top-k| / k` |
| **MRR** | How *high up* is the first right doc? (ranking) | mean of `1 / rank_of_first_gold` |

### Worked example

Query *"what is the cancellation policy?"*, gold = `[faq-cancel]`.

- Returns `[faq-cancel, faq-reschedule, faq-payment]` → hit@3=1, recall@3=1.0, precision@3=0.33, RR=1/1=1.0
- Returns `[faq-reschedule, faq-cancel, faq-payment]` → hit=1, recall=1.0, precision=0.33, RR=1/2=0.5
- Returns `[faq-reschedule, faq-payment, faq-booking]` (miss) → all 0

MRR is the average of RR across all questions. Rank 1 → 1.0, rank 2 → 0.5, rank 3 → 0.33, not found
→ 0. So MRR rewards putting the right doc *first*.

### Reading a scorecard

The deterministic **offline** gate (the `local` provider, reproducible with no keys) scores around:

```
hit_at_3 0.900   recall_at_3 0.900   mrr 0.900   precision_at_3 0.300
```

- **hit@3 = 0.90** — 9 of 10 questions had the correct doc in the top-3.
- **recall@3 = 0.90** — identical to hit@3 here *because each question has exactly one gold doc*.
  Recall and hit diverge only when a question has multiple relevant docs.
- **MRR = 0.90** — with hit@3 also 0.90, the 9 it found were all at **rank 1**.
- **precision@3 = 0.30** — looks low but is **capped**: with one gold doc and k=3, the ceiling is
  1/3 ≈ 0.33. That's why precision@3 is reported but **unthresholded** — a fixed threshold would be
  misleading. Precision matters when queries have several relevant docs or you want to punish noise.

With a real embedding provider the retrieval metrics rise to 1.0 on this corpus — sharper embeddings
rank the gold doc first every time.

### Which to care about

- **Recall/hit first.** If the right doc isn't retrieved, the model can't recover it — the answer is
  doomed. Extra irrelevant docs (lower precision) the model can usually ignore.
- **MRR**, because models weight earlier context more, and you often feed only the top few.
- **Precision** matters most with many retrieved chunks or multi-doc questions.

Retrieval metrics say nothing about whether the answer was correct or hallucinated — only whether the
right sources were available. That's the LLM-judge half.

## LLM-judge answer metrics

These grade the *generated answer* against the question and the retrieved context, using a model as
the grader (LLM-as-judge). Implemented in `ai-service/evals/judge.py`.

| Metric | Question it answers |
|---|---|
| **faithfulness** | Is every claim in the answer supported by the retrieved context? (catches hallucination / ungrounded statements) |
| **answer relevancy** | Does the answer actually address the question? |

Each metric prompts the judge model for a single score in `[0.0, 1.0]`. The judge is just a
`generate(...)` callable — the configured inference provider — so it needs a real generative model to
be meaningful (with the offline `local` provider the scores are degenerate). Score parsing is a pure
function (first number, clamped to `[0,1]`); if the model returns no number the metric defaults to
`0.0` rather than crashing, so a flaky judge fails closed.

These metrics are **opt-in** (`EVAL_JUDGE=1`) so the offline retrieval gate stays keyless. The judge
currently uses the same model that generated the answer — fine as a baseline; a separate, stronger
judge model is a natural improvement.

## Running it

```bash
# Retrieval gate, fully offline and deterministic (no keys, no database):
INFERENCE_PROVIDER=local make eval

# Full eval incl. LLM-judge answer metrics (needs a real provider/key):
EVAL_JUDGE=1 make eval-llm
```

The scorecard is written to `ai-service/evals/scorecard.{json,md}`. CI runs the offline retrieval
gate on every push.
