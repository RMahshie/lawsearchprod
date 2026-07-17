from __future__ import annotations

import json
from pathlib import Path

from tests.evals.e2e.report import _summary_stats, generate_report


def _result(
    question_id: str,
    *,
    expected_mode: str = "direct_account_amount",
    facts: list[dict] | None = None,
    expected: list[str] | None = None,
    actual: list[str] | None = None,
    score: int = 8,
) -> dict:
    expected = expected if expected is not None else ["AG"]
    actual = actual if actual is not None else ["AG"]
    return {
        "question_id": question_id,
        "question": f"Question {question_id}",
        "answer_mode": expected_mode,
        "expected_answer_mode": expected_mode,
        "actual_answer_mode": expected_mode,
        "classify_match": True,
        "expected_divisions": expected,
        "actual_divisions": actual,
        "route_match": set(expected) == set(actual),
        "judge": {
            "overall_score": score,
            "fact_checks": facts or [],
            "error_checks": [],
        },
        "provenance": {"passed": True},
    }


def test_summary_preserves_legacy_micro_and_defaults_missing_weights_to_one() -> None:
    results = [
        _result(
            "q1",
            facts=[{"fact": "core", "found": True}, {"fact": "detail", "found": False}],
        )
    ]

    stats = _summary_stats(results)

    assert stats["fact_recall_pct"] == 50.0
    assert stats["weighted_fact_recall_pct"] == 50.0
    assert stats["macro_fact_recall_pct"] == 50.0
    assert stats["fact_count"] == 2


def test_weighted_micro_and_macro_per_question_do_not_collapse_to_same_metric() -> None:
    results = [
        _result(
            "dense",
            facts=[
                {"fact": "important", "found": False, "weight": 2},
                {"fact": "minor-a", "found": True, "weight": 1},
                {"fact": "minor-b", "found": True, "weight": 1},
            ],
        ),
        _result(
            "short",
            facts=[{"fact": "important", "found": True, "weight": 2}],
        ),
    ]

    stats = _summary_stats(results)

    # Unweighted micro = 3/4; weighted micro = 4/6; macro = (2/3 + 1) / 2.
    assert stats["fact_recall_pct"] == 75.0
    assert stats["weighted_fact_recall_pct"] == round(4 / 6 * 100, 1)
    assert stats["macro_fact_recall_pct"] == round((2 / 3 + 1) / 2 * 100, 1)


def test_route_metrics_report_partial_credit_and_missing_extra_divisions() -> None:
    results = [
        _result("match", expected=["AG", "CJS"], actual=["AG", "CJS"]),
        _result("partial", expected=["AG", "EWD"], actual=["AG", "THUD"]),
    ]

    stats = _summary_stats(results)

    # TP=3, FP=1, FN=1; exact route accuracy remains 50%.
    assert stats["route_accuracy_pct"] == 50.0
    assert stats["route_precision_pct"] == 75.0
    assert stats["route_recall_pct"] == 75.0
    assert stats["route_f1_pct"] == 75.0
    assert stats["route_missing_count"] == 1
    assert stats["route_extra_count"] == 1


def test_generate_report_includes_expected_mode_macro_and_route_diagnostics(tmp_path: Path) -> None:
    results = [
        _result(
            "q1",
            expected_mode="direct_account_amount",
            facts=[{"fact": "a", "found": False, "fact_id": "f1", "weight": 2}],
            expected=["AG", "CJS"],
            actual=["AG"],
        ),
        _result(
            "q2",
            expected_mode="broad_topic_total",
            facts=[{"fact": "b", "found": True, "fact_id": "f2"}],
        ),
    ]

    generate_report(results, tmp_path)

    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Weighted Fact Recall (micro)" in report
    assert "| Expected Mode |" in report
    assert "Macro Recall" in report
    assert "Missing: ['CJS']" in report
    assert "Extra: none" in report
    assert json.loads((tmp_path / "raw_results.json").read_text()) == results


def test_summary_handles_empty_fact_and_route_denominators() -> None:
    stats = _summary_stats(
        [
            _result("empty", facts=[], expected=[], actual=[]),
        ]
    )

    assert stats["fact_recall_pct"] == 0.0
    assert stats["weighted_fact_recall_pct"] == 0.0
    assert stats["macro_fact_recall_pct"] == 0.0
    assert stats["route_precision_pct"] == 0.0
    assert stats["route_recall_pct"] == 0.0
    assert stats["route_f1_pct"] == 0.0


def test_macro_excludes_scored_questions_without_fact_checks() -> None:
    stats = _summary_stats(
        [
            _result("empty", facts=[]),
            _result("covered", facts=[{"fact": "a", "found": True}]),
        ]
    )

    assert stats["macro_fact_recall_pct"] == 100.0
