"""DeepSeek judge for e2e evals.

The judge is deliberately strict at the boundary.  Gold references are
normalised to stable criterion IDs before they are shown to the model and a
response is accepted only when it is valid JSON, validates against the schema,
and contains exactly the expected criterion sets.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, ValidationError

from app.services.llm_factory import ModelSpec, create_chat_model

logger = logging.getLogger(__name__)

JUDGE_MODEL = "deepseek-v4-pro"
JUDGE_REASONING = "high"
JUDGE_SPEC = ModelSpec(JUDGE_MODEL, provider="deepseek", reasoning_effort=JUDGE_REASONING)
MAX_JUDGE_ATTEMPTS = 2

MODE_STRUCTURAL_RULES: dict[str, str] = {
    "direct_account_amount": (
        "Lead with the main appropriation amount. Do not force a ledger, center-by-center "
        "figures, or user-fee line amounts unless the question asks for a breakdown. "
        "Name major uses as categories and do not add Included / Not Added Separately "
        "sections unless a breakdown was requested."
    ),
    "broad_topic_total": (
        "Group funding by agency/account and label financial types. Do not fabricate a "
        "summed total when financial types are mixed. Nest suballocations under their "
        "parent account rather than presenting them as top-level accounts."
    ),
    "funding_mechanism_no_amount": (
        "Do not hallucinate a dollar amount. Explain the funding mechanism (CR, "
        "rate-for-operations, apportionment, extension, or prior-law reference) and "
        "use a compact bottom-line plus mechanism bullets."
    ),
    "reconciliation_breakdown": (
        "Use Included / Not Added Separately sections when applicable. Preserve "
        "parent-child math and financial-type labels; do not double count parent "
        "totals and suballocations."
    ),
    "general_summary": (
        "Use concise prose or short bullets. Do not force a ledger or reconciliation "
        "table, and include dollar figures only when they directly explain the answer."
    ),
}


class _FactCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    fact_id: StrictStr
    found: StrictBool
    evidence: StrictStr


class _ErrorCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    error_id: StrictStr
    triggered: StrictBool
    evidence: StrictStr


class _RuleCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    rule_id: StrictStr
    passed: StrictBool
    evidence: StrictStr


class _StructuralChecks(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    passed: StrictBool
    issues: list[StrictStr] = Field(default_factory=list)
    rule_checks: list[_RuleCheck] = Field(default_factory=list)


class _JudgeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    fact_checks: list[_FactCheck]
    error_checks: list[_ErrorCheck]
    structural_checks: _StructuralChecks
    overall_score: StrictInt = Field(ge=0, le=10)
    reasoning: StrictStr


class JudgeResponseError(ValueError):
    """Raised when the judge cannot produce a valid, complete response."""


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return dict(value.model_dump(mode="json"))
    raise TypeError(f"Gold reference payload must be a mapping, got {type(value)!r}")


def _normalise_criterion(raw: Any, prefix: str, index: int) -> dict[str, Any]:
    """Return a stable criterion record while retaining legacy string golds."""
    if isinstance(raw, str):
        return {"id": f"{prefix}_{index:03d}", "statement": raw, "weight": 1}
    item = _as_dict(raw)
    criterion_id = item.get("id") or item.get(f"{prefix}_id") or item.get("criterion_id")
    statement = item.get("statement") or item.get("text") or item.get(prefix)
    if not criterion_id or not statement:
        raise ValueError(f"Gold {prefix} criterion {index} requires id and statement")
    weight = item.get("weight", 1)
    if isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0:
        raise ValueError(f"Gold criterion {criterion_id!r} must have a positive integer weight")
    result = {"id": str(criterion_id), "statement": str(statement), "weight": weight}
    for key in ("fact_type", "verification_status", "allowed_alternatives"):
        if key in item:
            result[key] = item[key]
    return result


def _gold_payload(
    gold: Any,
    expected_answer_mode: str = "",
    question_id: str | None = None,
) -> dict[str, Any]:
    """Consume ``GoldReference.to_judge_payload`` when available.

    The fallback keeps old result artifacts and third-party callers working,
    assigning deterministic IDs and unit weights to legacy strings.
    """
    if hasattr(gold, "to_judge_payload"):
        # The registry key is part of the stable-ID contract.  Older helper
        # objects may expose a zero-argument method, so retain that fallback.
        try:
            payload = gold.to_judge_payload(question_id) if question_id is not None else gold.to_judge_payload()
        except TypeError:
            payload = gold.to_judge_payload()
    elif hasattr(gold, "model_dump"):
        payload = gold.model_dump(mode="json")
    elif isinstance(gold, Mapping):
        payload = dict(gold)
    else:
        payload = {
            "required_facts": getattr(gold, "required_facts", []),
            "prohibited_errors": getattr(gold, "prohibited_errors", []),
            "structural_rules": getattr(gold, "structural_rules", []),
            "expected_answer_mode": getattr(gold, "expected_answer_mode", ""),
            "notes": getattr(gold, "notes", ""),
        }
    payload = _as_dict(payload)
    facts = payload.get("required_facts", payload.get("facts", [])) or []
    errors = payload.get("prohibited_errors", payload.get("errors", [])) or []
    rules = payload.get("structural_rules", payload.get("answer_shape_rules", [])) or []
    expected = payload.get("expected_answer_mode") or expected_answer_mode

    normalised_rules: list[dict[str, Any]] = []
    for index, raw in enumerate(rules):
        if isinstance(raw, str):
            normalised_rules.append({"id": f"rule_{index:03d}", "statement": raw, "weight": 1})
        else:
            item = _as_dict(raw)
            rule_id = item.get("id") or item.get("rule_id") or f"rule_{index:03d}"
            statement = item.get("statement") or item.get("text") or item.get("rule")
            if not statement:
                raise ValueError(f"Gold structural rule {rule_id!r} requires a statement")
            normalised_rules.append({"id": str(rule_id), "statement": str(statement), "weight": item.get("weight", 1)})
    # Mode rules always apply; Gold-specific shape rules supplement them.
    if (facts or errors or rules) and expected in MODE_STRUCTURAL_RULES and not any(item["id"] == f"mode:{expected}" for item in normalised_rules):
        normalised_rules.insert(0, {"id": f"mode:{expected}", "statement": MODE_STRUCTURAL_RULES[expected], "weight": 1})

    alternatives: list[dict[str, Any]] = []
    for index, raw in enumerate(payload.get("allowed_alternatives", []) or []):
        if isinstance(raw, str):
            alternatives.append({"id": f"alternative_{index:03d}", "statement": raw, "satisfies": []})
        else:
            item = _as_dict(raw)
            alternatives.append({
                "id": str(item.get("id") or f"alternative_{index:03d}"),
                "statement": str(item.get("statement") or item.get("text") or ""),
                "satisfies": list(item.get("satisfies", [])),
            })

    fact_records = [_normalise_criterion(raw, "fact", i) for i, raw in enumerate(facts)]
    error_records = [_normalise_criterion(raw, "error", i) for i, raw in enumerate(errors)]
    all_records = [*fact_records, *error_records, *normalised_rules]
    record_ids = [record["id"] for record in all_records]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("Gold criteria must have unique IDs")

    return {
        "required_facts": fact_records,
        "prohibited_errors": error_records,
        "structural_rules": normalised_rules,
        "allowed_alternatives": alternatives,
        "expected_answer_mode": expected,
        "notes": payload.get("notes", ""),
    }


def _criterion_block(criteria: Sequence[Mapping[str, Any]], *, prefix: str) -> str:
    if not criteria:
        return "(none)"
    lines = []
    for criterion in criteria:
        details = f" [{criterion.get('fact_type')}]" if criterion.get("fact_type") else ""
        satisfies = f" satisfies={','.join(criterion['satisfies'])}" if criterion.get("satisfies") else ""
        lines.append(f"- {criterion['id']} (weight={criterion.get('weight', 1)}){details}{satisfies}: {criterion['statement']}")
    return "\n".join(lines)


JUDGE_SYSTEM_PROMPT = """\
You are an expert evaluator of a RAG system answering questions about U.S. federal appropriations law (FY2026).

Evaluate every criterion by its stable ID. Return only one JSON object matching the exact schema below; do not use markdown fences,
omit criteria, add criteria, or change IDs. `expected_answer_mode` is the gold answer shape. `actual_answer_mode` is diagnostic only;
structural checks MUST use the expected mode's rules. Weight 2 marks a critical fact; weight 1 marks supporting detail. Credit allowed
alternatives as equivalent ways to satisfy their target fact IDs; they are not separate criteria and must not appear in `fact_checks`.

Schema:
{
  "fact_checks": [{"fact_id": "<id>", "found": true, "evidence": "<quote or not found>"}],
  "error_checks": [{"error_id": "<id>", "triggered": false, "evidence": "<quote or not triggered>"}],
  "structural_checks": {"passed": true, "issues": [], "rule_checks": [{"rule_id": "<id>", "passed": true, "evidence": "<quote or explanation>"}]},
  "overall_score": 0,
  "reasoning": "A concise 2-3 sentence summary."
}

Score the answer from 0 to 10: 10 means all required facts are present, no
prohibited errors are triggered, and structure is sound; 8-9 means nearly all
facts with no major error; 6-7 means most facts with one error or notable
structural issue; 4-5 means significant gaps or errors; 2-3 means major gaps;
0-1 means wrong or empty.
"""


def _build_judge_prompt(
    question: str,
    final_answer: str,
    answer_mode: str | None = None,
    gold: Any | None = None,
    *,
    expected_answer_mode: str | None = None,
    actual_answer_mode: str | None = None,
) -> str:
    """Build a prompt with distinct expected and actual modes.

    ``answer_mode`` remains an alias for the old API and is treated as the
    actual mode unless an explicit mode is supplied.
    """
    actual = actual_answer_mode or answer_mode or ""
    expected = expected_answer_mode or _gold_payload(gold or {}, answer_mode or "").get("expected_answer_mode", "")
    payload = _gold_payload(gold or {}, expected)
    return (
        f"## Question\n{question}\n\n"
        f"## Expected Answer Mode (use for structural rubric)\n{expected}\n\n"
        f"## Actual Answer Mode (diagnostic)\n{actual}\n\n"
        f"## Final Answer\n{final_answer}\n\n"
        f"## Gold Required Facts\n{_criterion_block(payload['required_facts'], prefix='fact')}\n\n"
        f"## Gold Prohibited Factual Errors\n{_criterion_block(payload['prohibited_errors'], prefix='error')}\n\n"
        f"## Expected-Mode Structural Rules\n{_criterion_block(payload['structural_rules'], prefix='rule')}\n\n"
        f"## Allowed Alternatives\n{_criterion_block(payload.get('allowed_alternatives', []), prefix='alternative')}\n\n"
        f"## Gold Notes\n{payload.get('notes') or '(none)'}"
    )


def _parse_judge_response(
    text: str,
    *,
    fact_ids: set[str] | None = None,
    error_ids: set[str] | None = None,
    rule_ids: set[str] | None = None,
) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        raw = json.loads(stripped)
    except (TypeError, json.JSONDecodeError) as exc:
        raise JudgeResponseError(f"Judge returned malformed JSON: {exc}") from exc
    if fact_ids is None and error_ids is None and rule_ids is None:
        return raw
    # The expected-mode rule is generated by this evaluator and namespaced as
    # ``mode:<answer_mode>``.  Some JSON-mode judges preserve every supplied
    # ID but drop only that synthetic namespace (or render it as ``mode_``).
    # Canonicalise those two unambiguous spellings before exact-set validation;
    # fact IDs, error IDs, and authored structural-rule IDs remain untouched.
    expected_mode_ids = {
        criterion_id
        for criterion_id in (rule_ids or set())
        if criterion_id.startswith("mode:")
    }
    if len(expected_mode_ids) == 1 and isinstance(raw, dict):
        expected_mode_id = next(iter(expected_mode_ids))
        answer_mode = expected_mode_id.removeprefix("mode:")
        mode_aliases = {answer_mode, f"mode_{answer_mode}"}
        structural = raw.get("structural_checks")
        if isinstance(structural, dict):
            checks = structural.get("rule_checks")
            if isinstance(checks, list):
                for check in checks:
                    if isinstance(check, dict) and check.get("rule_id") in mode_aliases:
                        check["rule_id"] = expected_mode_id
    try:
        parsed = _JudgeResponse.model_validate(raw)
    except ValidationError as exc:
        raise JudgeResponseError(f"Judge JSON failed schema validation: {exc}") from exc
    expected_sets = (fact_ids or set(), error_ids or set(), rule_ids or set())
    actual_lists = (
        [item.fact_id for item in parsed.fact_checks],
        [item.error_id for item in parsed.error_checks],
        [item.rule_id for item in parsed.structural_checks.rule_checks],
    )
    actual_sets = tuple(set(items) for items in actual_lists)
    if any(len(items) != len(set(items)) for items in actual_lists):
        raise JudgeResponseError("Judge response contains duplicate criterion IDs")
    if actual_sets != expected_sets:
        raise JudgeResponseError(
            "Judge response criterion IDs do not exactly match gold: "
            f"facts={sorted(actual_sets[0])}/{sorted(expected_sets[0])}, "
            f"errors={sorted(actual_sets[1])}/{sorted(expected_sets[1])}, "
            f"rules={sorted(actual_sets[2])}/{sorted(expected_sets[2])}"
        )
    rule_checks = parsed.structural_checks.rule_checks
    failed_rules = [item for item in rule_checks if not item.passed]
    if parsed.structural_checks.passed and failed_rules:
        raise JudgeResponseError("Structural checks cannot pass when a rule check failed")
    if not parsed.structural_checks.passed and not failed_rules and not parsed.structural_checks.issues:
        raise JudgeResponseError("Failed structural checks require an issue or failed rule")
    return parsed.model_dump(mode="json")


def _content(response: Any) -> str:
    value = getattr(response, "content", response)
    if isinstance(value, list):
        return "\n".join(str(block) for block in value)
    return str(value)


def _compatibility_result(
    parsed: dict[str, Any],
    payload: dict[str, Any],
    *,
    question_id: str,
    expected_mode: str,
    actual_mode: str,
    attempts: int,
) -> dict[str, Any]:
    facts_by_id = {item["id"]: item for item in payload["required_facts"]}
    errors_by_id = {item["id"]: item for item in payload["prohibited_errors"]}
    rules_by_id = {item["id"]: item for item in payload["structural_rules"]}
    fact_checks = []
    for item in parsed["fact_checks"]:
        criterion = facts_by_id[item["fact_id"]]
        fact_checks.append({**item, "fact": criterion["statement"], "weight": criterion["weight"]})
    error_checks = []
    for item in parsed["error_checks"]:
        criterion = errors_by_id[item["error_id"]]
        error_checks.append({**item, "error": criterion["statement"], "weight": criterion["weight"]})
    structural = parsed["structural_checks"]
    structural["rule_checks"] = [
        {**item, "rule": rules_by_id[item["rule_id"]]["statement"], "weight": rules_by_id[item["rule_id"]].get("weight", 1)}
        for item in structural.get("rule_checks", [])
    ]
    result = {
        "question_id": question_id,
        "expected_answer_mode": expected_mode,
        "actual_answer_mode": actual_mode,
        "answer_mode": actual_mode,  # historical report key
        "fact_checks": fact_checks,
        "error_checks": error_checks,
        "structural_checks": structural,
        "overall_score": parsed["overall_score"],
        "reasoning": parsed["reasoning"],
        "judge_metadata": {
            "model": JUDGE_MODEL,
            "reasoning_effort": JUDGE_REASONING,
            "attempts": attempts,
            "validated": True,
            "expected_answer_mode": expected_mode,
            "actual_answer_mode": actual_mode,
            "fact_count": len(payload["required_facts"]),
            "error_count": len(payload["prohibited_errors"]),
            "rule_count": len(payload["structural_rules"]),
        },
        "judge_model": JUDGE_MODEL,
        "judge_reasoning_effort": JUDGE_REASONING,
    }
    return result


def judge_answer(
    question_id: str,
    question: str,
    *args: Any,
    expected_answer_mode: str | None = None,
    actual_answer_mode: str | None = None,
    answer_mode: str | None = None,
    final_answer: str | None = None,
    gold: Any | None = None,
) -> dict[str, Any]:
    """Judge a final answer, accepting both legacy and explicit mode APIs.

    Legacy positional form: ``(question_id, question, actual_mode, answer, gold)``.
    Explicit positional form: ``(question_id, question, expected_mode, actual_mode,
    answer, gold)``.  New callers should use the explicit keyword arguments.
    """
    if args:
        if len(args) == 3:
            answer_mode, final_answer, gold = args
        elif len(args) == 4:
            expected_answer_mode, actual_answer_mode, final_answer, gold = args
        else:
            raise TypeError("judge_answer expects legacy 3 or explicit 4 arguments after question")
    if actual_answer_mode is None:
        actual_answer_mode = answer_mode or ""
    payload = _gold_payload(gold or {}, expected_answer_mode or actual_answer_mode, question_id)
    expected_answer_mode = expected_answer_mode or payload.get("expected_answer_mode") or actual_answer_mode
    if not payload["required_facts"] and not payload["prohibited_errors"] and not payload["structural_rules"]:
        return {
            "question_id": question_id,
            "expected_answer_mode": expected_answer_mode,
            "actual_answer_mode": actual_answer_mode,
            "answer_mode": actual_answer_mode,
            "fact_checks": [],
            "error_checks": [],
            "structural_checks": {"passed": True, "issues": ["No gold reference — skipped"], "rule_checks": []},
            "overall_score": -1,
            "reasoning": "No gold reference available; scoring skipped.",
            "judge_metadata": {
                "model": JUDGE_MODEL,
                "reasoning_effort": JUDGE_REASONING,
                "attempts": 0,
                "validated": True,
                "expected_answer_mode": expected_answer_mode,
                "actual_answer_mode": actual_answer_mode,
                "fact_count": 0,
                "error_count": 0,
                "rule_count": 0,
            },
        }

    llm = create_chat_model(JUDGE_MODEL, "e2e_eval", JUDGE_REASONING)
    judge_llm = llm.bind(response_format={"type": "json_object"})
    user_prompt = _build_judge_prompt(
        question,
        final_answer or "",
        expected_answer_mode=expected_answer_mode,
        actual_answer_mode=actual_answer_mode,
        gold=payload,
    )
    fact_ids = {item["id"] for item in payload["required_facts"]}
    error_ids = {item["id"] for item in payload["prohibited_errors"]}
    rule_ids = {item["id"] for item in payload["structural_rules"]}
    last_error: Exception | None = None
    for attempt in range(1, MAX_JUDGE_ATTEMPTS + 1):
        prompt = user_prompt
        if last_error is not None:
            prompt += (
                "\n\nYour previous response was rejected. Return only the exact JSON schema, with every criterion ID "
                f"exactly once. Validation error: {last_error}"
            )
        try:
            response = judge_llm.invoke([SystemMessage(content=JUDGE_SYSTEM_PROMPT), HumanMessage(content=prompt)])
            parsed = _parse_judge_response(_content(response), fact_ids=fact_ids, error_ids=error_ids, rule_ids=rule_ids)
            return _compatibility_result(
                parsed,
                payload,
                question_id=question_id,
                expected_mode=expected_answer_mode,
                actual_mode=actual_answer_mode,
                attempts=attempt,
            )
        except (JudgeResponseError, ValidationError, json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            logger.warning("Judge response attempt %d/%d rejected: %s", attempt, MAX_JUDGE_ATTEMPTS, exc)
    raise JudgeResponseError(f"Judge failed after {MAX_JUDGE_ATTEMPTS} attempts: {last_error}") from last_error
