"""DeepSeek judge for e2e eval — grades final answers against gold references."""

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

MODE_STRUCTURAL_RULES: dict[str, str] = {
    "direct_account_amount": (
        "- The answer should lead with the main appropriation amount.\n"
        "- No forced ledger, center-by-center figures, or user-fee line amounts "
        "unless the question specifically asks for a breakdown.\n"
        "- Major allowed uses should be named as categories, not dollar-by-dollar.\n"
        "- No Included / Not Added Separately sections unless breakdown was requested."
    ),
    "broad_topic_total": (
        "- Funding should be grouped by agency/account, not flattened into one list.\n"
        "- No fabricated summed total when financial types are mixed "
        "(e.g., grants + loan authority + loan subsidy should not be added into one number).\n"
        "- Each amount should be labeled by financial type where possible.\n"
        "- Suballocations should be nested under their parent account, not top-level."
    ),
    "funding_mechanism_no_amount": (
        "- No hallucinated dollar amount — if no explicit figure exists, say so.\n"
        "- The answer should explain the funding mechanism "
        "(CR, rate-for-operations, apportionment, extension, prior-law reference).\n"
        "- No Included / Not Added Separately sections or reconciliation tables.\n"
        "- Compact response: bottom-line + mechanism bullets."
    ),
    "reconciliation_breakdown": (
        "- Must have Included / Not Added Separately sections when applicable.\n"
        "- No double counting — parent totals and their suballocations should not both "
        "appear in Included.\n"
        "- Preserve parent-child math and financial-type labels.\n"
        "- Transfers, caps, limitations should be in Not Added Separately, not Included."
    ),
    "general_summary": (
        "- No forced ledger or reconciliation tables.\n"
        "- Concise prose or short bullets.\n"
        "- Dollar figures only when they directly explain the answer.\n"
        "- No Included / Not Added Separately sections unless explicitly requested."
    ),
}

JUDGE_SYSTEM_PROMPT = """\
You are an expert evaluator of a RAG system that answers questions about \
U.S. federal appropriations law (FY2026).

You will receive:
1. The user's question
2. The system's final answer
3. The answer_mode that was assigned
4. A gold standard reference containing:
   - required_facts: facts the answer MUST contain
   - prohibited_errors: specific mistakes to flag
   - notes: additional context
5. Mode-specific structural rules the answer should follow

Your job is to evaluate the final answer against the gold reference.

## Evaluation steps

### Fact checks
For each required_fact in the gold reference, determine whether the answer \
contains that fact (or a reasonable paraphrase). Cite the specific evidence \
from the answer, or note its absence.

### Error checks
For each prohibited_error, determine whether the answer commits that error. \
Cite the specific evidence if triggered.

### Structural checks
Evaluate whether the answer follows the mode-specific structural rules. \
Note any violations.

### Overall score (0-10)
- 10: All required facts present, no prohibited errors, perfect structure
- 8-9: Nearly all facts, no major errors, minor structural issues
- 6-7: Most facts present, one error or notable structural issue
- 4-5: Significant fact gaps or errors
- 2-3: Major gaps and errors
- 0-1: Answer is wrong or empty

## Output format

Return valid JSON matching this exact schema:
{
    "fact_checks": [
        {"fact": "<required fact text>", "found": true/false, "evidence": "<quote or 'not found'>"}
    ],
    "error_checks": [
        {"error": "<prohibited error text>", "triggered": true/false, "evidence": "<quote or 'not triggered'>"}
    ],
    "structural_checks": {
        "passed": true/false,
        "issues": ["<issue description>", ...]
    },
    "overall_score": <int 0-10>,
    "reasoning": "<2-3 sentence summary of the evaluation>"
}

Do not wrap the JSON in markdown fences. Return only the JSON object."""


def _build_judge_prompt(
    question: str,
    final_answer: str,
    answer_mode: str,
    gold: dict[str, Any],
) -> str:
    facts_block = "\n".join(f"- {f}" for f in gold.get("required_facts", []))
    errors_block = "\n".join(f"- {e}" for e in gold.get("prohibited_errors", []))
    notes = gold.get("notes", "")
    structural_rules = MODE_STRUCTURAL_RULES.get(answer_mode, "No mode-specific rules.")

    return (
        f"## Question\n{question}\n\n"
        f"## Answer Mode\n{answer_mode}\n\n"
        f"## Final Answer\n{final_answer}\n\n"
        f"## Gold Reference\n\n"
        f"### Required Facts\n{facts_block or '(none specified)'}\n\n"
        f"### Prohibited Errors\n{errors_block or '(none specified)'}\n\n"
        f"### Notes\n{notes or '(none)'}\n\n"
        f"## Mode-Specific Structural Rules\n{structural_rules}"
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


def judge_answer(
    question_id: str,
    question: str,
    answer_mode: str,
    final_answer: str,
    gold: dict[str, Any],
) -> dict[str, Any]:
    """Judge a final answer against its gold reference using DeepSeek v4 pro.

    Args:
        question_id: Unique question identifier.
        question: The original user question.
        answer_mode: The classify stage output (or gold expected mode).
        final_answer: The pipeline's final markdown answer.
        gold: Dict with required_facts, prohibited_errors, notes keys.

    Returns:
        Full judge result dict with question metadata added.
    """
    if not gold.get("required_facts") and not gold.get("prohibited_errors"):
        return {
            "question_id": question_id,
            "fact_checks": [],
            "error_checks": [],
            "structural_checks": {"passed": True, "issues": ["No gold reference — skipped"]},
            "overall_score": -1,
            "reasoning": "No gold reference available; scoring skipped.",
        }

    llm = create_chat_model(JUDGE_MODEL, "e2e_eval", JUDGE_REASONING)
    judge_llm = llm.bind(response_format={"type": "json_object"})

    user_prompt = _build_judge_prompt(question, final_answer, answer_mode, gold)
    parse_error: json.JSONDecodeError | None = None
    result: dict[str, Any] | None = None

    for attempt in range(2):
        prompt = user_prompt
        if parse_error is not None:
            prompt = (
                f"{user_prompt}\n\n"
                "Your previous response was invalid JSON. Return only valid JSON for the exact schema. "
                f"JSON parse error: {parse_error}"
            )
        messages = [
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = judge_llm.invoke(messages)
        content = getattr(response, "content", response)
        if isinstance(content, list):
            content = "\n".join(str(block) for block in content)
        content = str(content).strip()

        try:
            result = _parse_judge_response(content)
            break
        except json.JSONDecodeError as exc:
            parse_error = exc
            if attempt == 1:
                raise

    if result is None:
        raise ValueError("Judge returned no parseable result")
    result["question_id"] = question_id

    return result
