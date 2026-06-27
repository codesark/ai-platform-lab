"""LLM-as-judge answer metrics: faithfulness and answer relevancy.

Each metric prompts a judge model to return a single score in [0.0, 1.0]:

  faithfulness     — is every claim in the answer supported by the retrieved
                     context? (catches hallucination / ungrounded statements)
  answer_relevancy — does the answer actually address the question?

These need a real generative provider (e.g. Gemini). They are *not* meaningful
with the offline `local` provider (its templated output ignores the prompt), so
they run only when EVAL_JUDGE is set and a real provider is configured.

The judge is just a callable `generate(prompt, **kwargs) -> str` (the inference
provider). Score parsing is a pure function so it can be unit-tested offline.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable

Generate = Callable[..., Awaitable[str]]

_SCORE_RE = re.compile(r"\d+(?:\.\d+)?")

_FAITHFULNESS_PROMPT = """You are grading whether an ANSWER is faithful to the CONTEXT.
Faithful means every factual claim in the answer is supported by the context, with
nothing invented or contradicted. Reply with ONLY a number from 0.0 (not faithful at
all) to 1.0 (fully supported). No words.

CONTEXT:
{context}

ANSWER:
{answer}

Score:"""

_RELEVANCY_PROMPT = """You are grading whether an ANSWER addresses the QUESTION.
Reply with ONLY a number from 0.0 (does not address it) to 1.0 (directly and fully
answers it). No words.

QUESTION:
{question}

ANSWER:
{answer}

Score:"""


def parse_score(text: str) -> float | None:
    """Extract the first numeric score from a judge reply, clamped to [0.0, 1.0]."""
    match = _SCORE_RE.search(text)
    if match is None:
        return None
    try:
        value = float(match.group(0))
    except ValueError:
        return None
    return max(0.0, min(1.0, value))


async def _judge(prompt: str, generate: Generate) -> float:
    # Deterministic judging; no tight max_tokens cap — some models (e.g. gemini-2.5
    # thinking) spend output budget before the number, and parse_score takes the
    # first number anyway, so extra text is harmless.
    raw = await generate(prompt, temperature=0.0)
    score = parse_score(raw)
    return score if score is not None else 0.0


async def faithfulness(context: str, answer: str, generate: Generate) -> float:
    return await _judge(_FAITHFULNESS_PROMPT.format(context=context, answer=answer), generate)


async def answer_relevancy(question: str, answer: str, generate: Generate) -> float:
    return await _judge(_RELEVANCY_PROMPT.format(question=question, answer=answer), generate)
