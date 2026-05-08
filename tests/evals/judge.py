"""DeepSeek judge for evaluating retrieved chunk relevance."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_factory import ModelSpec, create_chat_model

logger = logging.getLogger(__name__)

JUDGE_MODEL = "deepseek-v4-pro"
JUDGE_REASONING = "high"
JUDGE_SPEC = ModelSpec(JUDGE_MODEL, provider="deepseek", reasoning_effort=JUDGE_REASONING)

JUDGE_SYSTEM_PROMPT = """\
You are an expert evaluator of retrieval quality for a RAG system that answers \
questions about U.S. federal appropriations law (FY2026).

You will receive:
1. A user question
2. The answer_mode that classifies what kind of answer is expected
3. The division (subcommittee) being searched
4. A set of retrieved text chunks from that division's vector store

Your job is to evaluate how well this set of chunks supports answering the question \
for the given answer_mode.

## Tier definitions

Classify each chunk into exactly one tier:

**direct** — The chunk directly contains information needed to answer the user's \
question for this answer_mode. For direct_account_amount: the named account's amount \
or allowed uses. For broad_topic_total: funding lanes for the requested topic. For \
funding_mechanism_no_amount: mechanism language (CR, rate-for-operations, extensions). \
For reconciliation_breakdown: parent totals, child allocations, fee sources, transfers. \
For general_summary: provisions that directly explain the answer.

**adjacent** — The chunk is related to the topic but not clearly within the requested \
scope. Nearby provisions, sibling accounts, contextual information that could support \
but doesn't directly answer.

**not_responsive** — The chunk was retrieved but contains no information useful for \
answering this question. Wrong topic, wrong account, irrelevant boilerplate.

## Coverage score (0-10)

After classifying each chunk, provide a holistic coverage score:
- 10: The chunk set contains everything needed for an excellent answer
- 7-9: Most critical information present, minor gaps
- 4-6: Some relevant chunks but significant gaps in coverage
- 1-3: Mostly irrelevant chunks, critical information missing
- 0: No relevant chunks at all

## Output format

Return valid JSON matching this exact schema:
{
    "chunk_assessments": [
        {
            "chunk_index": <int>,
            "tier": "direct" | "adjacent" | "not_responsive",
            "reason": "<1 sentence explaining why>"
        }
    ],
    "coverage_score": <int 0-10>,
    "coverage_gaps": "<what's missing for this answer_mode, or 'none' if complete>",
    "tier_counts": {
        "direct": <int>,
        "adjacent": <int>,
        "not_responsive": <int>
    }
}

Do not wrap the JSON in markdown fences. Return only the JSON object."""


def _build_judge_prompt(
    question: str,
    answer_mode: str,
    division: str,
    division_acronym: str,
    chunks: list[dict[str, Any]],
) -> str:
    chunk_texts = []
    for i, chunk in enumerate(chunks):
        content = chunk.get("content", "")
        score = chunk.get("score", "n/a")
        chunk_texts.append(f"--- Chunk {i} (similarity score: {score}) ---\n{content}")

    chunks_block = "\n\n".join(chunk_texts)

    return (
        f"Question: {question}\n\n"
        f"Answer mode: {answer_mode}\n\n"
        f"Division: {division} [{division_acronym}]\n\n"
        f"Retrieved chunks ({len(chunks)} total):\n\n{chunks_block}"
    )


def _parse_judge_response(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return json.loads(stripped)


def judge_chunks(
    question: str,
    answer_mode: str,
    division: str,
    division_acronym: str,
    embedding_model: str,
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Judge a set of retrieved chunks using DeepSeek v4 pro.

    Returns the full judge result dict with question/model metadata added.
    """
    if not chunks:
        return {
            "question": question,
            "answer_mode": answer_mode,
            "division": division,
            "division_acronym": division_acronym,
            "embedding_model": embedding_model,
            "chunk_assessments": [],
            "coverage_score": 0,
            "coverage_gaps": "No chunks retrieved",
            "tier_counts": {"direct": 0, "adjacent": 0, "not_responsive": 0},
        }

    llm = create_chat_model(JUDGE_MODEL, "eval", JUDGE_REASONING)
    judge_llm = llm.bind(response_format={"type": "json_object"})

    user_prompt = _build_judge_prompt(
        question, answer_mode, division, division_acronym, chunks,
    )

    messages = [
        SystemMessage(content=JUDGE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = judge_llm.invoke(messages)
    content = getattr(response, "content", response)
    if isinstance(content, list):
        content = "\n".join(str(block) for block in content)
    content = str(content).strip()

    result = _parse_judge_response(content)

    result["question"] = question
    result["answer_mode"] = answer_mode
    result["division"] = division
    result["division_acronym"] = division_acronym
    result["embedding_model"] = embedding_model

    if "tier_counts" not in result and "chunk_assessments" in result:
        counts = {"direct": 0, "adjacent": 0, "not_responsive": 0}
        for assessment in result["chunk_assessments"]:
            tier = assessment.get("tier", "not_responsive")
            counts[tier] = counts.get(tier, 0) + 1
        result["tier_counts"] = counts

    return result
