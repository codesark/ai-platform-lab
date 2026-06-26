"""Run the retrieval eval and write a scorecard (JSON + Markdown).

Builds an in-memory index from the corpus using the SAME embeddings as production
(via the configured inference provider), so it runs anywhere — no Postgres needed,
which keeps it usable as a CI gate. Set INFERENCE_PROVIDER=local for a deterministic
offline run. Exits non-zero if any metric is below its threshold.
"""

from __future__ import annotations

import asyncio
import json
import math
import pathlib

from evals.metrics import hit_at_k, precision_at_k, recall_at_k, reciprocal_rank
from inference import embed

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
CORPUS = _ROOT / "corpus" / "faq.jsonl"
DATASET = _HERE / "dataset.jsonl"
SCORECARD_JSON = _HERE / "scorecard.json"
SCORECARD_MD = _HERE / "scorecard.md"

K = 3
THRESHOLDS = {"hit_at_3": 0.8, "recall_at_3": 0.8, "mrr": 0.6}


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def _load_jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


async def _build_index() -> list[tuple[str, list[float]]]:
    index: list[tuple[str, list[float]]] = []
    for rec in _load_jsonl(CORPUS):
        body = f"Q: {rec['question']}\nA: {rec['answer']}"
        index.append((rec["id"], await embed(body)))
    return index


async def _retrieve(query: str, index: list[tuple[str, list[float]]], k: int) -> list[str]:
    qv = await embed(query)
    ranked = sorted(index, key=lambda item: _cosine(qv, item[1]), reverse=True)
    return [doc_id for doc_id, _ in ranked[:k]]


def _render_md(agg: dict[str, float], passed: bool, n: int) -> str:
    lines = [
        "# Retrieval eval scorecard",
        "",
        f"Examples: {n}  |  Status: {'PASS' if passed else 'FAIL'}",
        "",
        "| Metric | Score | Threshold |",
        "|---|---|---|",
    ]
    for metric, threshold in THRESHOLDS.items():
        lines.append(f"| {metric} | {agg[metric]:.3f} | {threshold:.2f} |")
    lines.append(f"| precision_at_3 | {agg['precision_at_3']:.3f} | — |")
    return "\n".join(lines) + "\n"


async def main() -> int:
    index = await _build_index()
    examples = _load_jsonl(DATASET)

    rows: list[dict[str, object]] = []
    hits: list[float] = []
    recalls: list[float] = []
    precisions: list[float] = []
    rrs: list[float] = []

    for ex in examples:
        expected = list(ex["expected_doc_ids"])
        retrieved = await _retrieve(str(ex["question"]), index, K)
        h = hit_at_k(expected, retrieved, K)
        rc = recall_at_k(expected, retrieved, K)
        pr = precision_at_k(expected, retrieved, K)
        rr = reciprocal_rank(expected, retrieved)
        hits.append(h)
        recalls.append(rc)
        precisions.append(pr)
        rrs.append(rr)
        rows.append(
            {
                "id": ex["id"],
                "question": ex["question"],
                "expected": expected,
                "retrieved": retrieved,
                "hit_at_3": h,
                "recall_at_3": rc,
                "reciprocal_rank": rr,
            }
        )

    n = len(examples)
    agg = {
        "hit_at_3": sum(hits) / n,
        "recall_at_3": sum(recalls) / n,
        "precision_at_3": sum(precisions) / n,
        "mrr": sum(rrs) / n,
    }
    passed = all(agg[metric] >= threshold for metric, threshold in THRESHOLDS.items())

    scorecard = {"metrics": agg, "thresholds": THRESHOLDS, "passed": passed, "examples": rows}
    SCORECARD_JSON.write_text(json.dumps(scorecard, indent=2))
    SCORECARD_MD.write_text(_render_md(agg, passed, n))
    print(_render_md(agg, passed, n))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
