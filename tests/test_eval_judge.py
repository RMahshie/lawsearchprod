from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests.evals.e2e import judge


class _Gold:
    expected_answer_mode = "direct_account_amount"

    def to_judge_payload(self):
        return {
            "expected_answer_mode": self.expected_answer_mode,
            "required_facts": [
                {"id": "fact.amount", "statement": "The account receives $10", "weight": 2, "fact_type": "direct"},
            ],
            "prohibited_errors": [
                {"id": "error.add", "statement": "Do not add fee authority", "weight": 1},
            ],
            "structural_rules": [
                {"id": "rule.lead", "statement": "Lead with the account amount", "weight": 1},
            ],
            "allowed_alternatives": [
                {"id": "alt.amount", "statement": "A reasonable paraphrase is allowed", "satisfies": ("fact.amount",)},
            ],
        }


def _response(*, fact_id="fact.amount", error_id="error.add", rule_id="rule.lead", include_mode_rule=True):
    rules = [{"rule_id": rule_id, "passed": True, "evidence": "amount leads"}]
    if include_mode_rule:
        rules.insert(0, {"rule_id": "mode:direct_account_amount", "passed": True, "evidence": "shape is compact"})
    return {
        "fact_checks": [{"fact_id": fact_id, "found": True, "evidence": "$10"}],
        "error_checks": [{"error_id": error_id, "triggered": False, "evidence": "not triggered"}],
        "structural_checks": {
            "passed": True,
            "issues": [],
            "rule_checks": rules,
        },
        "overall_score": 10,
        "reasoning": "All criteria are satisfied.",
    }


class _FakeJudge:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def bind(self, **_kwargs):
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=next(self.responses))


def test_build_prompt_uses_expected_mode_rubric_separately_from_actual():
    prompt = judge._build_judge_prompt(
        "What amount?",
        "The account receives $10.",
        expected_answer_mode="reconciliation_breakdown",
        actual_answer_mode="general_summary",
        gold=_Gold(),
    )
    assert "Expected Answer Mode (use for structural rubric)\nreconciliation_breakdown" in prompt
    assert "Actual Answer Mode (diagnostic)\ngeneral_summary" in prompt
    assert "rule.lead" in prompt
    assert "alt.amount" in prompt


def test_judge_consumes_to_judge_payload_and_preserves_legacy_keys(monkeypatch):
    fake = _FakeJudge([__import__("json").dumps(_response())])
    monkeypatch.setattr(judge, "create_chat_model", lambda *args, **kwargs: fake)

    result = judge.judge_answer(
        "q1",
        "What amount?",
        expected_answer_mode="direct_account_amount",
        actual_answer_mode="general_summary",
        final_answer="The account receives $10.",
        gold=_Gold(),
    )

    assert result["expected_answer_mode"] == "direct_account_amount"
    assert result["actual_answer_mode"] == "general_summary"
    assert result["fact_checks"][0]["fact_id"] == "fact.amount"
    assert result["fact_checks"][0]["fact"] == "The account receives $10"
    assert result["fact_checks"][0]["weight"] == 2
    assert result["judge_metadata"]["validated"] is True


def test_judge_retries_malformed_json(monkeypatch):
    fake = _FakeJudge(["not json", __import__("json").dumps(_response())])
    monkeypatch.setattr(judge, "create_chat_model", lambda *args, **kwargs: fake)

    result = judge.judge_answer("q1", "What amount?", "direct_account_amount", "The account receives $10.", _Gold())

    assert result["overall_score"] == 10
    assert result["judge_metadata"]["attempts"] == 2
    assert len(fake.calls) == 2


def test_judge_rejects_wrong_criterion_set_after_retry(monkeypatch):
    fake = _FakeJudge([
        __import__("json").dumps(_response(fact_id="fact.wrong")),
        __import__("json").dumps(_response(fact_id="fact.wrong")),
    ])
    monkeypatch.setattr(judge, "create_chat_model", lambda *args, **kwargs: fake)

    with pytest.raises(judge.JudgeResponseError, match="criterion IDs"):
        judge.judge_answer("q1", "What amount?", "direct_account_amount", "The account receives $10.", _Gold())


def test_parse_rejects_duplicate_ids_even_when_set_matches():
    value = _response()
    value["fact_checks"].append(value["fact_checks"][0].copy())
    with pytest.raises(judge.JudgeResponseError, match="duplicate"):
        judge._parse_judge_response(
            __import__("json").dumps(value),
            fact_ids={"fact.amount"},
            error_ids={"error.add"},
            rule_ids={"rule.lead", "mode:direct_account_amount"},
        )


@pytest.mark.parametrize("alias", ["direct_account_amount", "mode_direct_account_amount"])
def test_parse_canonicalises_only_synthetic_mode_rule_aliases(alias):
    value = _response()
    value["structural_checks"]["rule_checks"][0]["rule_id"] = alias

    parsed = judge._parse_judge_response(
        __import__("json").dumps(value),
        fact_ids={"fact.amount"},
        error_ids={"error.add"},
        rule_ids={"rule.lead", "mode:direct_account_amount"},
    )

    assert parsed["structural_checks"]["rule_checks"][0]["rule_id"] == "mode:direct_account_amount"


def test_parse_still_rejects_wrong_authored_rule_id():
    value = _response(rule_id="direct_account_amount")
    with pytest.raises(judge.JudgeResponseError, match="criterion IDs"):
        judge._parse_judge_response(
            __import__("json").dumps(value),
            fact_ids={"fact.amount"},
            error_ids={"error.add"},
            rule_ids={"rule.lead", "mode:direct_account_amount"},
        )


def test_no_gold_reference_keeps_legacy_skip_shape(monkeypatch):
    monkeypatch.setattr(judge, "create_chat_model", lambda *_args, **_kwargs: pytest.fail("must not call judge"))
    result = judge.judge_answer(
        "q-empty",
        "Question",
        expected_answer_mode="direct_account_amount",
        actual_answer_mode="general_summary",
        final_answer="Answer",
        gold={},
    )
    assert result["overall_score"] == -1
    assert result["structural_checks"]["rule_checks"] == []


def test_parse_rejects_inconsistent_structural_summary():
    value = _response()
    value["structural_checks"]["passed"] = True
    value["structural_checks"]["rule_checks"][0]["passed"] = False
    with pytest.raises(judge.JudgeResponseError, match="Structural checks cannot pass"):
        judge._parse_judge_response(
            __import__("json").dumps(value),
            fact_ids={"fact.amount"},
            error_ids={"error.add"},
            rule_ids={"rule.lead", "mode:direct_account_amount"},
        )
