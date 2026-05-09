"""Report generation for e2e eval results.

Produces 4 levels:
1. Overall summary — fact recall %, error rate, avg score, classify/route accuracy
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


def _scored_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter to results that have gold references (score != -1)."""
    return [r for r in results if r.get("judge", {}).get("overall_score", -1) >= 0]


def _summary_stats(results: list[dict[str, Any]]) -> dict[str, Any]:
    scored = _scored_results(results)
    if not scored:
        return {
            "count": len(results),
            "scored": 0,
            "avg_score": 0.0,
            "fact_recall_pct": 0.0,
            "error_rate_pct": 0.0,
            "classify_accuracy_pct": 0.0,
            "route_accuracy_pct": 0.0,
        }

    scores = [r["judge"]["overall_score"] for r in scored]

    total_facts = 0
    found_facts = 0
    total_errors = 0
    triggered_errors = 0
    for r in scored:
        for fc in r["judge"].get("fact_checks", []):
            total_facts += 1
            if fc.get("found"):
                found_facts += 1
        for ec in r["judge"].get("error_checks", []):
            total_errors += 1
            if ec.get("triggered"):
                triggered_errors += 1

    classify_correct = sum(1 for r in results if r.get("classify_match"))
    route_correct = sum(1 for r in results if r.get("route_match"))

    return {
        "count": len(results),
        "scored": len(scored),
        "avg_score": round(_avg(scores), 1),
        "fact_recall_pct": round(_pct(found_facts, total_facts), 1),
        "error_rate_pct": round(_pct(triggered_errors, total_errors), 1),
        "classify_accuracy_pct": round(_pct(classify_correct, len(results)), 1),
        "route_accuracy_pct": round(_pct(route_correct, len(results)), 1),
    }


def generate_report(results: list[dict[str, Any]], output_dir: Path) -> None:
    """Generate 4-level markdown report and raw JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "raw_results.json").write_text(
        json.dumps(results, indent=2, default=str),
        encoding="utf-8",
    )

    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in results:
        by_mode[r["answer_mode"]].append(r)

    lines: list[str] = []

    # Level 1: Overall summary
    overall = _summary_stats(results)
    lines.append("# E2E Eval Report\n")
    lines.append("## Overall Summary\n")
    lines.append(f"- **Questions**: {overall['count']} ({overall['scored']} scored)")
    lines.append(f"- **Avg Score**: {overall['avg_score']} / 10")
    lines.append(f"- **Fact Recall**: {overall['fact_recall_pct']}%")
    lines.append(f"- **Error Rate**: {overall['error_rate_pct']}%")
    lines.append(f"- **Classify Accuracy**: {overall['classify_accuracy_pct']}%")
    lines.append(f"- **Route Accuracy**: {overall['route_accuracy_pct']}%")
    lines.append("")

    # Level 2: By answer_mode
    lines.append("## By Answer Mode\n")
    lines.append("| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |")
    lines.append("|------|-------|-----------|-------------|------------|----------|-------|")
    for mode in sorted(by_mode.keys()):
        s = _summary_stats(by_mode[mode])
        lines.append(
            f"| {mode} | {s['count']} | {s['avg_score']} | "
            f"{s['fact_recall_pct']}% | {s['error_rate_pct']}% | "
            f"{s['classify_accuracy_pct']}% | {s['route_accuracy_pct']}% |"
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
        if not r.get("route_match"):
            lines.append(f"  - Expected: {expected_divs}")
            lines.append(f"  - Actual: {actual_divs}")

        judge = r.get("judge", {})

        missed = [fc["fact"] for fc in judge.get("fact_checks", []) if not fc.get("found")]
        if missed:
            lines.append("\n**Missed Facts**:")
            for f in missed:
                lines.append(f"- {f}")

        triggered = [ec for ec in judge.get("error_checks", []) if ec.get("triggered")]
        if triggered:
            lines.append("\n**Triggered Errors**:")
            for ec in triggered:
                lines.append(f"- {ec['error']}: {ec.get('evidence', '')}")

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
