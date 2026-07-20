from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.evals.e2e.provenance import evaluate_provenance
from tests.evals.e2e.report import _summary_stats, generate_report
from tests.evals.e2e.run import run_pipeline
from tests.evals.questions import EvalQuestion


def _source_annotation(
    annotation_id: str,
    figure: str,
    value: float,
    chunk_id: str,
) -> dict[str, Any]:
    return {
        "id": annotation_id,
        "kind": "source",
        "figure": figure,
        "value": value,
        "label": f"Source for {figure}",
        "source": {"chunk_id": chunk_id},
    }


def _chunk(chunk_id: str, content: str) -> dict[str, Any]:
    return {"chunk_id": chunk_id, "content": content}


def _issue_codes(result: dict[str, Any]) -> set[str]:
    return {issue["code"] for issue in result["issues"]}


def test_source_provenance_passes_with_visible_marker_and_retrieved_chunk() -> None:
    result = evaluate_provenance(
        {
            "final_answer": "The account receives $1,000 [[num:src_a]].",
            "division_answers": [],
            "number_annotations": [
                _source_annotation("src_a", "$1,000", 1_000, "chunk-a")
            ],
            "retrieved_chunks": [_chunk("chunk-a", "The account receives $1,000.")],
        }
    )

    assert result["passed"] is True
    assert result["answer_marker_count"] == 1
    assert result["source_annotation_count"] == 1
    assert result["issues"] == []


def test_visible_figure_and_marker_failures_are_diagnostic() -> None:
    result = evaluate_provenance(
        {
            "final_answer": "The amount is $1,000, with [[num:missing]] support.",
            "division_answers": [],
            "number_annotations": [],
            "retrieved_chunks": [],
        }
    )

    assert result["passed"] is False
    assert {"unmarked_figure", "detached_marker", "unknown_marker"} <= _issue_codes(result)


def test_source_annotation_must_resolve_to_chunk_containing_its_value() -> None:
    annotation = _source_annotation("src_a", "$1,000", 1_000, "chunk-a")
    base = {
        "final_answer": "$1,000 [[num:src_a]] is provided.",
        "division_answers": [],
        "number_annotations": [annotation],
    }

    missing_chunk = evaluate_provenance({**base, "retrieved_chunks": []})
    wrong_value = evaluate_provenance(
        {**base, "retrieved_chunks": [_chunk("chunk-a", "Only $2,000 is stated.")]}
    )

    assert "source_chunk_not_retrieved" in _issue_codes(missing_chunk)
    assert "source_value_not_in_chunk" in _issue_codes(wrong_value)


def test_derived_provenance_passes_when_inputs_resolve_and_reconcile() -> None:
    result = evaluate_provenance(
        {
            "final_answer": "The combined amount is $3,000 [[num:drv_total]].",
            "division_answers": [
                {
                    "division": "Test Division",
                    "division_acronym": "TD",
                    "answer": (
                        "Account A has $1,000 [[num:src_a]] and Account B has "
                        "$2,000 [[num:src_b]]."
                    ),
                }
            ],
            "number_annotations": [
                _source_annotation("src_a", "$1,000", 1_000, "chunk-a"),
                _source_annotation("src_b", "$2,000", 2_000, "chunk-b"),
                {
                    "id": "drv_total",
                    "kind": "derived",
                    "figure": "$3,000",
                    "value": 3_000,
                    "label": "Combined amount",
                    "derived": {
                        "equation": "$1,000 + $2,000 = $3,000",
                        "input_ids": ["src_a", "src_b"],
                        "source_input_ids": ["src_a", "src_b"],
                    },
                },
            ],
            "retrieved_chunks": [
                _chunk("chunk-a", "Account A has $1,000."),
                _chunk("chunk-b", "Account B has $2,000."),
            ],
        }
    )

    assert result["passed"] is True
    assert result["derived_annotation_count"] == 1


def test_derived_provenance_reports_unknown_inputs_and_bad_arithmetic() -> None:
    unknown_inputs = evaluate_provenance(
        {
            "final_answer": "$3,000 [[num:drv_total]] is the total.",
            "division_answers": [],
            "number_annotations": [
                {
                    "id": "drv_total",
                    "kind": "derived",
                    "figure": "$3,000",
                    "value": 3_000,
                    "label": "Total",
                    "derived": {
                        "equation": "$1,000 + $2,000 = $3,000",
                        "input_ids": ["missing"],
                        "source_input_ids": [],
                    },
                }
            ],
            "retrieved_chunks": [],
        }
    )

    bad_total = evaluate_provenance(
        {
            "final_answer": "$4,000 [[num:drv_total]] is the total.",
            "division_answers": [
                {
                    "division": "Test Division",
                    "division_acronym": "TD",
                    "answer": "$1,000 [[num:src_a]] plus $2,000 [[num:src_b]].",
                }
            ],
            "number_annotations": [
                _source_annotation("src_a", "$1,000", 1_000, "chunk-a"),
                _source_annotation("src_b", "$2,000", 2_000, "chunk-b"),
                {
                    "id": "drv_total",
                    "kind": "derived",
                    "figure": "$4,000",
                    "value": 4_000,
                    "label": "Incorrect total",
                    "derived": {
                        "equation": "$1,000 + $2,000 = $4,000",
                        "input_ids": ["src_a", "src_b"],
                        "source_input_ids": ["src_a", "src_b"],
                    },
                },
            ],
            "retrieved_chunks": [
                _chunk("chunk-a", "$1,000 is provided."),
                _chunk("chunk-b", "$2,000 is provided."),
            ],
        }
    )

    assert {"derived_input_unknown", "derived_source_inputs_missing"} <= _issue_codes(
        unknown_inputs
    )
    assert "derived_value_mismatch" in _issue_codes(bad_total)


def test_derived_source_inputs_must_match_immediate_input_lineage() -> None:
    result = evaluate_provenance(
        {
            "final_answer": "$2,000 [[num:drv_total]] is the stated total.",
            "division_answers": [
                {
                    "division": "Test Division",
                    "division_acronym": "TD",
                    "answer": "$1,000 [[num:src_a]] and $2,000 [[num:src_b]].",
                }
            ],
            "number_annotations": [
                _source_annotation("src_a", "$1,000", 1_000, "chunk-a"),
                _source_annotation("src_b", "$2,000", 2_000, "chunk-b"),
                {
                    "id": "drv_total",
                    "kind": "derived",
                    "figure": "$2,000",
                    "value": 2_000,
                    "label": "Incorrect lineage",
                    "derived": {
                        "equation": "$2,000 = $2,000",
                        "input_ids": ["src_a"],
                        "source_input_ids": ["src_b"],
                    },
                },
            ],
            "retrieved_chunks": [
                _chunk("chunk-a", "$1,000 is provided."),
                _chunk("chunk-b", "$2,000 is provided."),
            ],
        }
    )

    assert "derived_source_inputs_mismatch" in _issue_codes(result)


def test_run_pipeline_validates_full_chunks_but_stores_only_previews() -> None:
    graph_result = {
        "answer_mode": "direct_account_amount",
        "selected_divisions": [],
        "division_answers": [],
        "final_answer": "$1,000 [[num:src_a]] is provided.",
        "number_annotations": [
            _source_annotation("src_a", "$1,000", 1_000, "chunk-a")
        ],
        "retrieved_chunks": [
            {
                "chunk_id": "chunk-a",
                "division": "Test Division",
                "division_acronym": "TD",
                "content": "x" * 800 + " The account receives $1,000.",
            }
        ],
        "mapped_chunks": [],
    }

    class FakeGraph:
        def invoke(self, _state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
            assert config == {"recursion_limit": 50}
            return graph_result

    class FakeService:
        _graph = FakeGraph()

    output = run_pipeline(
        FakeService(),  # type: ignore[arg-type]
        EvalQuestion("test", "What amount is provided?", "direct_account_amount"),
        vector_store_id="store",
        embedding_model="model",
        thinking_speed="normal",
        k=1,
        vectorstore_root="/tmp/store",
    )

    assert output["provenance"]["passed"] is True
    assert "content" not in output["retrieved_chunks"][0]
    assert output["retrieved_chunks"][0]["content_preview"].endswith("...")


def test_report_aggregates_and_renders_provenance(tmp_path: Path) -> None:
    results = [
        {
            "question_id": "q1",
            "question": "What is provided?",
            "answer_mode": "direct_account_amount",
            "expected_answer_mode": "direct_account_amount",
            "actual_answer_mode": "direct_account_amount",
            "classify_match": True,
            "expected_divisions": [],
            "actual_divisions": [],
            "route_match": True,
            "provenance": {"passed": True, "issues": []},
            "judge": {
                "overall_score": 8,
                "fact_checks": [],
                "error_checks": [],
                "structural_checks": {"passed": True, "issues": []},
            },
        },
        {
            "question_id": "q2",
            "question": "What is missing?",
            "answer_mode": "direct_account_amount",
            "expected_answer_mode": "direct_account_amount",
            "actual_answer_mode": "direct_account_amount",
            "classify_match": True,
            "expected_divisions": [],
            "actual_divisions": [],
            "route_match": True,
            "provenance": {
                "passed": False,
                "issues": [
                    {
                        "code": "unmarked_figure",
                        "scope": "answer",
                        "detail": "figure=$1,000",
                    }
                ],
            },
            "judge": {
                "overall_score": 6,
                "fact_checks": [],
                "error_checks": [],
                "structural_checks": {"passed": True, "issues": []},
            },
        },
    ]

    stats = _summary_stats(results)
    generate_report(results, tmp_path)
    report = (tmp_path / "report.md").read_text(encoding="utf-8")

    assert stats["provenance_checked"] == 2
    assert stats["provenance_pass_rate_pct"] == 50.0
    assert "**Provenance Pass Rate**: 50.0% (2 checked)" in report
    assert "**Provenance**: FAIL" in report
    assert "`unmarked_figure` (answer): figure=$1,000" in report
