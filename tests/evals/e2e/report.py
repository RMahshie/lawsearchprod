"""Report generation for e2e eval results.

Produces 4 levels:
1. Overall summary — fact recall %, error rate, provenance, avg score, classify/route accuracy
2. By answer_mode — same metrics grouped by question type
3. Per-question detail — expected vs actual, score, missed facts, triggered errors
4. Raw JSON — full pipeline state + judge output
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _avg(values: list[float | int]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pct(count: int, total: int) -> float:
    return (count / total * 100) if total else 0.0


def _ratio(numerator: float, denominator: float) -> float:
    """Return a ratio, using zero for an empty denominator.

    Report generation must remain useful for reference/partial runs where a
    bucket can legitimately contain no facts or no routed Divisions.
    """
    return numerator / denominator if denominator else 0.0


def _fact_weight(fact_check: dict[str, Any]) -> float:
    """Read a fact importance weight while accepting legacy judge output.

    Historical raw results have no ``weight`` field.  They intentionally count
    as weight 1, as do malformed/non-positive values so that one old result
    cannot make a report fail to render.
    """
    value = fact_check.get("weight", fact_check.get("importance_weight", 1))
    try:
        weight = float(value)
    except (TypeError, ValueError):
        return 1.0
    return weight if weight > 0 else 1.0


def _fact_recall(result: dict[str, Any]) -> tuple[int, int, float, float]:
    """Return unweighted/weighted found and total fact counts for one result."""
    checks = result.get("judge", {}).get("fact_checks", [])
    found = sum(1 for check in checks if check.get("found", check.get("present", False)))
    total = len(checks)
    weighted_total = sum(_fact_weight(check) for check in checks)
    weighted_found = sum(
        _fact_weight(check)
        for check in checks
        if check.get("found", check.get("present", False))
    )
    return found, total, weighted_found, weighted_total


def _route_sets(result: dict[str, Any]) -> tuple[set[Any], set[Any]]:
    """Return expected and actual route sets, tolerating old/missing shapes."""
    expected = result.get("expected_divisions") or []
    actual = result.get("actual_divisions") or []
    return set(expected), set(actual)


def _route_diagnostics(result: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    expected, actual = _route_sets(result)
    return sorted(expected - actual), sorted(actual - expected)


def _macro_fact_recall_by_expected_mode(
    results: list[dict[str, Any]],
) -> dict[str, float]:
    """Compute equal-question fact recall for each expected answer mode."""
    grouped: dict[str, list[float]] = defaultdict(list)
    for result in _scored_results(results):
        found, total, _weighted_found, _weighted_total = _fact_recall(result)
        mode = result.get("expected_answer_mode") or result.get("answer_mode") or "unknown"
        # Keep the mode visible even when every question in it has no facts;
        # those questions are excluded from the macro denominator and the mode
        # reports 0.0 when its resulting population is empty.
        if total:
            grouped[mode].append(found / total)
        else:
            grouped.setdefault(mode, [])
    return {
        mode: round(_avg(recalls) * 100, 1)
        for mode, recalls in sorted(grouped.items())
    }


def _scored_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter to results that have gold references (score != -1)."""
    return [r for r in results if r.get("judge", {}).get("overall_score", -1) >= 0]


def _summary_stats(results: list[dict[str, Any]]) -> dict[str, Any]:
    scored = _scored_results(results)
    scores = [r["judge"]["overall_score"] for r in scored]

    total_facts = 0
    found_facts = 0
    weighted_total_facts = 0.0
    weighted_found_facts = 0.0
    question_recalls: list[float] = []
    total_errors = 0
    triggered_errors = 0
    for r in scored:
        found, total, weighted_found, weighted_total = _fact_recall(r)
        total_facts += total
        found_facts += found
        weighted_total_facts += weighted_total
        weighted_found_facts += weighted_found
        # A scored question with no fact checks has an undefined denominator;
        # exclude it from the macro population.  An all-empty population still
        # reports 0.0 through _avg's zero-denominator behavior.
        if total:
            question_recalls.append(found / total)
        for ec in r["judge"].get("error_checks", []):
            total_errors += 1
            if ec.get("triggered", ec.get("present", False)):
                triggered_errors += 1

    classify_correct = sum(1 for r in results if r.get("classify_match"))
    route_correct = sum(1 for r in results if r.get("route_match"))
    route_true_positive = 0
    route_false_positive = 0
    route_false_negative = 0
    route_missing_count = 0
    route_extra_count = 0
    missing_divisions: dict[str, int] = defaultdict(int)
    extra_divisions: dict[str, int] = defaultdict(int)
    for r in results:
        missing, extra = _route_diagnostics(r)
        route_missing_count += len(missing)
        route_extra_count += len(extra)
        for division in missing:
            missing_divisions[str(division)] += 1
        for division in extra:
            extra_divisions[str(division)] += 1
        route_false_negative += len(missing)
        route_false_positive += len(extra)
        expected, actual = _route_sets(r)
        route_true_positive += len(expected & actual)
    route_precision = _ratio(
        route_true_positive, route_true_positive + route_false_positive
    )
    route_recall = _ratio(
        route_true_positive, route_true_positive + route_false_negative
    )
    route_f1 = _ratio(2 * route_precision * route_recall, route_precision + route_recall)
    provenance_results = [
        r["provenance"]
        for r in results
        if isinstance(r.get("provenance"), dict)
        and isinstance(r["provenance"].get("passed"), bool)
    ]
    provenance_passed = sum(1 for result in provenance_results if result["passed"])

    unweighted_recall = _pct(found_facts, total_facts)
    weighted_recall = _ratio(weighted_found_facts, weighted_total_facts) * 100
    macro_recall = _avg(question_recalls) * 100
    macro_by_expected_mode = _macro_fact_recall_by_expected_mode(results)

    stats = {
        "count": len(results),
        "scored": len(scored),
        "avg_score": round(_avg(scores), 1),
        # Keep this historical micro metric unchanged for comparison with
        # previously generated reports.
        "fact_recall_pct": round(unweighted_recall, 1),
        "weighted_fact_recall_pct": round(weighted_recall, 1),
        "macro_fact_recall_pct": round(macro_recall, 1),
        "macro_fact_recall_by_expected_mode": macro_by_expected_mode,
        "fact_count": total_facts,
        "found_fact_count": found_facts,
        "weighted_fact_total": round(weighted_total_facts, 3),
        "weighted_found_fact_total": round(weighted_found_facts, 3),
        "error_rate_pct": round(_pct(triggered_errors, total_errors), 1),
        "classify_accuracy_pct": round(_pct(classify_correct, len(results)), 1),
        "route_accuracy_pct": round(_pct(route_correct, len(results)), 1),
        "route_true_positive_count": route_true_positive,
        "route_false_positive_count": route_false_positive,
        "route_false_negative_count": route_false_negative,
        "route_missing_count": route_missing_count,
        "route_extra_count": route_extra_count,
        "route_missing_divisions": dict(sorted(missing_divisions.items())),
        "route_extra_divisions": dict(sorted(extra_divisions.items())),
        "route_precision_pct": round(route_precision * 100, 1),
        "route_recall_pct": round(route_recall * 100, 1),
        "route_f1_pct": round(route_f1 * 100, 1),
        "provenance_checked": len(provenance_results),
        "provenance_pass_rate_pct": (
            round(_pct(provenance_passed, len(provenance_results)), 1)
            if provenance_results
            else None
        ),
    }
    return stats


def _provenance_pct(stats: dict[str, Any]) -> str:
    value = stats["provenance_pass_rate_pct"]
    return f"{value}%" if value is not None else "n/a"


def generate_report(results: list[dict[str, Any]], output_dir: Path) -> None:
    """Generate 4-level markdown report and raw JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "raw_results.json").write_text(
        json.dumps(results, indent=2, default=str),
        encoding="utf-8",
    )

    # Group diagnostics by the expected mode.  A classifier miss should not
    # move a question into the wrong structural/fact-recall bucket.
    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in results:
        mode = r.get("expected_answer_mode") or r.get("answer_mode") or "unknown"
        by_mode[mode].append(r)

    lines: list[str] = []

    # Level 1: Overall summary
    overall = _summary_stats(results)
    lines.append("# E2E Eval Report\n")
    lines.append("## Overall Summary\n")
    lines.append(f"- **Questions**: {overall['count']} ({overall['scored']} scored)")
    lines.append(f"- **Avg Score**: {overall['avg_score']} / 10")
    lines.append(f"- **Fact Recall**: {overall['fact_recall_pct']}%")
    lines.append(
        f"- **Weighted Fact Recall (micro)**: {overall['weighted_fact_recall_pct']}%"
    )
    lines.append(
        f"- **Fact Recall (macro per question)**: {overall['macro_fact_recall_pct']}%"
    )
    lines.append(f"- **Error Rate**: {overall['error_rate_pct']}%")
    lines.append(f"- **Classify Accuracy**: {overall['classify_accuracy_pct']}%")
    lines.append(f"- **Route Accuracy**: {overall['route_accuracy_pct']}%")
    lines.append(
        f"- **Route Precision / Recall / F1**: {overall['route_precision_pct']}% / "
        f"{overall['route_recall_pct']}% / {overall['route_f1_pct']}%"
    )
    lines.append(
        f"- **Route Missing / Extra Divisions**: {overall['route_missing_count']} / "
        f"{overall['route_extra_count']}"
    )
    lines.append(
        f"- **Provenance Pass Rate**: {_provenance_pct(overall)} "
        f"({overall['provenance_checked']} checked)"
    )
    lines.append("")

    # Level 2: By answer_mode
    lines.append("## By Answer Mode\n")
    lines.append(
        "| Expected Mode | Count | Avg Score | Fact Recall | Weighted Recall | "
        "Macro Recall | Error Rate | Classify | Route | Route P/R/F1 | Provenance |"
    )
    lines.append(
        "|---------------|-------|-----------|-------------|-----------------|--------------|------------|----------|-------|-------------|------------|"
    )
    for mode in sorted(by_mode.keys()):
        s = _summary_stats(by_mode[mode])
        lines.append(
            f"| {mode} | {s['count']} | {s['avg_score']} | "
            f"{s['fact_recall_pct']}% | {s['weighted_fact_recall_pct']}% | "
            f"{s['macro_fact_recall_pct']}% | {s['error_rate_pct']}% | "
            f"{s['classify_accuracy_pct']}% | {s['route_accuracy_pct']}% | "
            f"{s['route_precision_pct']}% / {s['route_recall_pct']}% / "
            f"{s['route_f1_pct']}% | "
            f"{_provenance_pct(s)} |"
        )
    lines.append("")

    # Level 3: Per-question detail
    lines.append("## Per-Question Detail\n")
    for r in results:
        qid = r["question_id"]
        score = r.get("judge", {}).get("overall_score", "n/a")
        lines.append(f"### {qid} (score: {score})\n")

        short_q = r["question"][:120]
        lines.append(f"**Question**: {short_q}")
        lines.append(f"**Answer Mode**: expected={r.get('expected_answer_mode', '?')} "
                      f"actual={r.get('actual_answer_mode', '?')} "
                      f"{'MATCH' if r.get('classify_match') else 'MISMATCH'}")

        expected_divs = sorted(r.get("expected_divisions", []))
        actual_divs = sorted(r.get("actual_divisions", []))
        lines.append(f"**Route**: {'MATCH' if r.get('route_match') else 'MISMATCH'}")
        missing_divisions, extra_divisions = _route_diagnostics(r)
        if not r.get("route_match") or missing_divisions or extra_divisions:
            lines.append(f"  - Expected: {expected_divs}")
            lines.append(f"  - Actual: {actual_divs}")
            lines.append(f"  - Missing: {missing_divisions or 'none'}")
            lines.append(f"  - Extra: {extra_divisions or 'none'}")

        provenance = r.get("provenance")
        if isinstance(provenance, dict) and isinstance(provenance.get("passed"), bool):
            lines.append(f"**Provenance**: {'PASS' if provenance['passed'] else 'FAIL'}")
            for issue in provenance.get("issues", []):
                lines.append(
                    f"  - `{issue.get('code', 'unknown')}` "
                    f"({issue.get('scope', 'unknown')}): {issue.get('detail', '')}"
                )
        else:
            lines.append("**Provenance**: NOT CHECKED")

        judge = r.get("judge", {})

        missed = [
            fc.get("fact", fc.get("fact_id", "unknown fact"))
            for fc in judge.get("fact_checks", [])
            if not fc.get("found", fc.get("present", False))
        ]
        if missed:
            lines.append("\n**Missed Facts**:")
            for f in missed:
                lines.append(f"- {f}")

        triggered = [
            ec
            for ec in judge.get("error_checks", [])
            if ec.get("triggered", ec.get("present", False))
        ]
        if triggered:
            lines.append("\n**Triggered Errors**:")
            for ec in triggered:
                lines.append(
                    f"- {ec.get('error', ec.get('error_id', 'unknown error'))}: "
                    f"{ec.get('evidence', '')}"
                )

        structural = judge.get("structural_checks", {})
        if not structural.get("passed", True):
            lines.append("\n**Structural Issues**:")
            for issue in structural.get("issues", []):
                lines.append(f"- {issue}")

        reasoning = judge.get("reasoning", "")
        if reasoning:
            lines.append(f"\n**Judge Reasoning**: {reasoning}")

        lines.append("")

    report_text = "\n".join(lines)
    (output_dir / "report.md").write_text(report_text, encoding="utf-8")
