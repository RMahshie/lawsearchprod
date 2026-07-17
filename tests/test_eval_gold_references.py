from __future__ import annotations

import pytest

from tests.evals.e2e.gold_references import (
    GOLD_REFERENCES,
    CorpusScope,
    GoldFact,
    SourceEvidence,
    AnswerShapeRule,
    GoldReference,
    validate_gold_references,
)
from tests.evals.questions import EVAL_QUESTIONS


def test_registry_is_complete_and_source_traceable() -> None:
    validate_gold_references()
    assert set(GOLD_REFERENCES) == {question.id for question in EVAL_QUESTIONS}
    for question_id, reference in GOLD_REFERENCES.items():
        payload = reference.to_judge_payload(question_id)
        assert payload["required_facts"]
        assert all(item["id"].startswith(f"{question_id}-fact-") for item in payload["required_facts"])
        assert all(item["weight"] in (1, 2) for item in payload["required_facts"])
        assert all(item["evidence"] or item["corpus_scope"] for item in payload["required_facts"])
        assert all(item["id"].startswith(f"{question_id}-error-") for item in payload["prohibited_errors"])
        for item in payload["required_facts"]:
            for evidence in item["evidence"]:
                assert evidence["source_file"].startswith("data/bills/2026/")
                assert evidence["line_start"] <= evidence["line_end"]


def test_absence_and_derived_facts_have_explicit_metadata() -> None:
    recon = GOLD_REFERENCES["recon_2"].to_judge_payload("recon_2")["required_facts"]
    assert any(item["fact_type"] == "derived" and item["equation"] for item in recon)
    mechanism = GOLD_REFERENCES["mechanism_3"].to_judge_payload("mechanism_3")["required_facts"]
    absent = [item for item in mechanism if item["fact_type"] == "absence"]
    assert absent and all(item["corpus_scope"]["bills"] for item in absent)
    assert absent[0]["corpus_scope"]["search_query"]
    complete_absent = [fact for fact in GOLD_REFERENCES["recon_5"].facts if fact.fact_type == "absence"]
    assert complete_absent and set(complete_absent[0].corpus_scope.bills) == {"PL37", "PL74", "PL75"}
    for question_id in ("broad_1", "broad_5"):
        assert all(fact.fact_type != "absence" for fact in GOLD_REFERENCES[question_id].facts if "clean" in fact.statement.lower())


def test_criterion_ids_are_statement_stable_when_order_changes() -> None:
    reference = GOLD_REFERENCES["direct_1"]
    first = [item["id"] for item in reference.to_judge_payload("direct_1")["required_facts"]]
    reordered = GoldReference(
        required_facts=list(reversed(reference.required_facts)),
        prohibited_errors=reference.prohibited_errors,
        expected_answer_mode=reference.expected_answer_mode,
        expected_divisions=reference.expected_divisions,
    )
    second = [item["id"] for item in reordered.to_judge_payload("direct_1")["required_facts"]]
    assert set(first) == set(second)


def test_major_audit_corrections_are_present() -> None:
    direct_5 = " ".join(GOLD_REFERENCES["direct_5"].required_facts)
    assert "$59,858,000,000" in direct_5 and "$75,039,000,000" in direct_5
    assert "pooled across" in direct_5

    broad_2 = " ".join(GOLD_REFERENCES["broad_2"].required_facts)
    assert "Community Development Block Grants" in broad_2
    assert "HOME Investment Partnerships" in broad_2

    broad_3 = " ".join(GOLD_REFERENCES["broad_3"].required_facts)
    broad_3_errors = " ".join(GOLD_REFERENCES["broad_3"].prohibited_errors)
    assert "terminal" not in broad_3.lower()
    assert "terminal-upgrade construction amount" in broad_3_errors

    broad_4 = " ".join(GOLD_REFERENCES["broad_4"].required_facts)
    assert "OJP includes $84,000,000" in broad_4
    assert "COPS includes $84,000,000" not in broad_4


def test_minor_audit_corrections_are_present() -> None:
    text = {
        question_id: " ".join(reference.required_facts)
        for question_id, reference in GOLD_REFERENCES.items()
    }
    errors = {
        question_id: " ".join(reference.prohibited_errors)
        for question_id, reference in GOLD_REFERENCES.items()
    }

    assert "no fewer than 148 FTE" in text["direct_2"]
    assert "$20,000,000 Alaska" in text["direct_4"]
    assert "$9,000,000 Toxic Substances Control Act" in text["direct_4"]
    assert "February 13, 2026" in text["mechanism_2"]
    assert "does not state a new consolidated full-year dollar total" in text["mechanism_2"]
    assert "only as an inference" in text["mechanism_4"]
    assert "Apportionment" in text["mechanism_5"]
    assert "$24,438,336,000" in text["recon_2"]
    assert "conflicting Science" not in text["recon_2"] + errors["recon_2"]
    assert "does not label this entire lane as water infrastructure" in text["recon_4"]
    assert "No statutory IRS parent total" in text["recon_5"]
    assert "$11,195,365,000" in text["recon_5"]
    assert "inspection, and regulatory activities" in text["summary_1"]
    assert "electronic prescribing" not in text["summary_1"] + errors["summary_1"]
    assert "Office of Science" in text["summary_2"]
    assert "NNSA" in text["summary_2"]
    assert "Army Corps" in text["summary_2"]
    assert "Army Corps of Engineers" in text["summary_3"]


def test_reconciliation_equations_are_explicit() -> None:
    for question_id, needle in (
        ("recon_1", "= $6,957,972,000"),
        ("recon_2", "= $24,438,336,000"),
        ("recon_5", "= $11,195,365,000"),
    ):
        equations = [fact.equation for fact in GOLD_REFERENCES[question_id].facts if fact.fact_type == "derived"]
        assert any(equation and needle in equation and not equation.startswith("Source-backed") for equation in equations)


def test_answer_shape_rules_are_separate_from_required_facts() -> None:
    recon_4 = GOLD_REFERENCES["recon_4"]
    assert all("answer should" not in str(fact).lower() for fact in recon_4.required_facts)
    assert any(isinstance(rule, AnswerShapeRule) for rule in recon_4.structural_rules)
    for reference in GOLD_REFERENCES.values():
        assert all("route outside" not in str(error).lower() for error in reference.prohibited_errors)


def test_compact_questions_do_not_require_optional_detail() -> None:
    direct_4 = " ".join(GOLD_REFERENCES["direct_4"].required_facts)
    assert "Geographic Programs" not in direct_4
    assert "Geographic Programs" in GOLD_REFERENCES["direct_4"].notes
    assert len(GOLD_REFERENCES["broad_2"].required_facts) <= 11


def test_validation_rejects_unscoped_absence_claim() -> None:
    bad = GoldReference(
        required_facts=[GoldFact(id="bad", statement="No amount appears in the source", fact_type="absence")],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[EVAL_QUESTIONS[0].divisions[0]],
    )
    refs = dict(GOLD_REFERENCES)
    refs["direct_1"] = bad
    with pytest.raises(ValueError, match="absence claims require a corpus scope"):
        validate_gold_references(refs)


def test_validation_rejects_incomplete_absence_scope() -> None:
    original = GOLD_REFERENCES["direct_1"].facts[0]
    bad = GoldFact(
        id="bad",
        statement="No amount appears in the source",
        fact_type="absence",
        evidence=original.evidence,
        corpus_scope=CorpusScope(
            bills=("PL37",),
            source_files=(original.evidence[0].source_file,),
            search_query="amount",
        ),
    )
    refs = dict(GOLD_REFERENCES)
    refs["direct_1"] = GoldReference(
        required_facts=[bad],
        expected_answer_mode=GOLD_REFERENCES["direct_1"].expected_answer_mode,
        expected_divisions=GOLD_REFERENCES["direct_1"].expected_divisions,
    )
    with pytest.raises(ValueError, match="absence scope must be complete"):
        validate_gold_references(refs)


def test_validation_rejects_affirmative_fact_without_evidence() -> None:
    refs = dict(GOLD_REFERENCES)
    refs["direct_1"] = GoldReference(
        required_facts=[GoldFact(id="bad", statement="An unsupported fact")],
        expected_answer_mode=GOLD_REFERENCES["direct_1"].expected_answer_mode,
        expected_divisions=GOLD_REFERENCES["direct_1"].expected_divisions,
    )
    with pytest.raises(ValueError, match="affirmative facts require source evidence"):
        validate_gold_references(refs)


def test_validation_rejects_fact_still_needing_review() -> None:
    original = GOLD_REFERENCES["direct_1"].facts[0]
    refs = dict(GOLD_REFERENCES)
    refs["direct_1"] = GoldReference(
        required_facts=[
            GoldFact(
                id="needs-review",
                statement=original.statement,
                verification_status="needs_review",
                evidence=original.evidence,
            )
        ],
        expected_answer_mode=GOLD_REFERENCES["direct_1"].expected_answer_mode,
        expected_divisions=GOLD_REFERENCES["direct_1"].expected_divisions,
    )
    with pytest.raises(ValueError, match="criterion is not verified"):
        validate_gold_references(refs)


def test_validation_rejects_anchor_outside_source_range() -> None:
    original = GOLD_REFERENCES["direct_1"].facts[0]
    bad_fact = GoldFact(
        id="tampered",
        statement=original.statement,
        evidence=(
            SourceEvidence(
                bill="PL37",
                division=original.evidence[0].division,
                locator=original.evidence[0].locator,
                source_file=original.evidence[0].source_file,
                line_start=original.evidence[0].line_start,
                line_end=original.evidence[0].line_end,
                anchor="anchor not in source",
                excerpt=original.evidence[0].excerpt,
                source_hash=original.evidence[0].source_hash,
            ),
        ),
    )
    refs = dict(GOLD_REFERENCES)
    refs["direct_1"] = GoldReference(
        required_facts=[bad_fact],
        prohibited_errors=GOLD_REFERENCES["direct_1"].prohibited_errors,
        expected_answer_mode=GOLD_REFERENCES["direct_1"].expected_answer_mode,
        expected_divisions=GOLD_REFERENCES["direct_1"].expected_divisions,
    )
    with pytest.raises(ValueError, match="source anchor is absent"):
        validate_gold_references(refs)
