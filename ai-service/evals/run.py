"""Run the eval and write a scorecard (JSON + Markdown).

Retrieval metrics (hit@k, recall@k, precision@k, MRR) always run. They build an
in-memory index from the corpus using the SAME embeddings as production (via the
configured inference provider), so they run anywhere — no Postgres needed — which
keeps them usable as a CI gate. Set INFERENCE_PROVIDER=local for a deterministic
offline run.

Set EVAL_JUDGE=1 to additionally run LLM-judge answer metrics (faithfulness,
answer relevancy). These generate an answer per question and grade it with the
judge model, so they need a real generative provider (e.g. Gemini) to be
meaningful — with the `local` provider they run but the scores are degenerate.

Exits non-zero if any enabled metric is below its threshold.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import pathlib

from agent.tools.retrieve import RetrievedChunk
from evals.judge import answer_relevancy, faithfulness
from evals.metrics import hit_at_k, precision_at_k, recall_at_k, reciprocal_rank
from inference import embed, generate
from rag.prompt import build_grounded_prompt

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
CORPUS = _ROOT / "corpus" / "faq.jsonl"
DATASET = _HERE / "dataset.jsonl"
SCORECARD_JSON = _HERE / "scorecard.json"
SCORECARD_MD = _HERE / "scorecard.md"

K = 3
RETRIEVAL_THRESHOLDS = {"hit_at_3": 0.8, "recall_at_3": 0.8, "mrr": 0.6}
JUDGE_THRESHOLDS = {"faithfulness": 0.7, "answer_relevancy": 0.7}
# precision_at_3 is reported but unthresholded: with one gold doc per question and
# k=3 its ceiling is ~0.33, so a fixed threshold would be misleading.


def _judge_enabled() -> bool:
    return os.environ.get("EVAL_JUDGE", "").strip().lower() in {"1", "true", "yes", "on"}


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def _load_jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


async def _build_index() -> list[tuple[str, str, list[float]]]:
    """Return (doc_id, text, embedding) per corpus record."""
    index: list[tuple[str, str, list[float]]] = []
    for rec in _load_jsonl(CORPUS):
        body = f"Q: {rec['question']}\nA: {rec['answer']}"
        index.append((rec["id"], body, await embed(body)))
    return index


async def _retrieve(
    query: str, index: list[tuple[str, str, list[float]]], k: int
) -> list[tuple[str, str]]:
    """Return the top-k (doc_id, text) ranked by cosine similarity to the query."""
    qv = await embed(query)
    ranked = sorted(index, key=lambda item: _cosine(qv, item[2]), reverse=True)
    return [(doc_id, text) for doc_id, text, _ in ranked[:k]]


def _render_md(
    agg: dict[str, float], thresholds: dict[str, float], passed: bool, n: int, judge: bool
) -> str:
    status = "PASS" if passed else "FAIL"
    lines = [
        "# Eval scorecard",
        "",
        f"Examples: {n}  |  LLM-judge: {'on' if judge else 'off'}  |  Status: {status}",
        "",
        "| Metric | Score | Threshold |",
        "|---|---|---|",
    ]
    for metric, score in agg.items():
        threshold = thresholds.get(metric)
        cell = f"{threshold:.2f}" if threshold is not None else "—"
        lines.append(f"| {metric} | {score:.3f} | {cell} |")
    return "\n".join(lines) + "\n"


async def main() -> int:
    judge = _judge_enabled()
    index = await _build_index()
    examples = _load_jsonl(DATASET)

    acc: dict[str, list[float]] = {
        "hit_at_3": [],
        "recall_at_3": [],
        "precision_at_3": [],
        "mrr": [],
    }
    if judge:
        acc["faithfulness"] = []
        acc["answer_relevancy"] = []

    rows: list[dict[str, object]] = []
    for ex in examples:
        question = str(ex["question"])
        expected = list(ex["expected_doc_ids"])
        retrieved = await _retrieve(question, index, K)
        retrieved_ids = [doc_id for doc_id, _ in retrieved]

        acc["hit_at_3"].append(hit_at_k(expected, retrieved_ids, K))
        acc["recall_at_3"].append(recall_at_k(expected, retrieved_ids, K))
        acc["precision_at_3"].append(precision_at_k(expected, retrieved_ids, K))
        acc["mrr"].append(reciprocal_rank(expected, retrieved_ids))

        row: dict[str, object] = {
            "id": ex["id"],
            "question": ex["question"],
            "expected": expected,
            "retrieved": retrieved_ids,
        }

        if judge:
            chunks = [
                RetrievedChunk(doc_id=d, chunk_id=0, source="eval", score=1.0, text=t)
                for d, t in retrieved
            ]
            answer = await generate(build_grounded_prompt(question, chunks))
            context = "\n\n".join(t for _, t in retrieved)
            faith = await faithfulness(context, answer, generate)
            relevancy = await answer_relevancy(question, answer, generate)
            acc["faithfulness"].append(faith)
            acc["answer_relevancy"].append(relevancy)
            row["faithfulness"] = faith
            row["answer_relevancy"] = relevancy

        rows.append(row)

    n = len(examples)
    agg = {metric: sum(values) / n for metric, values in acc.items()}

    thresholds = dict(RETRIEVAL_THRESHOLDS)
    if judge:
        thresholds.update(JUDGE_THRESHOLDS)
    passed = all(agg[metric] >= threshold for metric, threshold in thresholds.items())

    scorecard = {
        "metrics": agg,
        "thresholds": thresholds,
        "judge": judge,
        "passed": passed,
        "examples": rows,
    }
    SCORECARD_JSON.write_text(json.dumps(scorecard, indent=2))
    SCORECARD_MD.write_text(_render_md(agg, thresholds, passed, n, judge))
    print(_render_md(agg, thresholds, passed, n, judge))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
