"""Report generation for embedding eval results."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _avg(values: list[float | int]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pct(count: int, total: int) -> float:
    return (count / total * 100) if total else 0.0


def _model_stats(results: list[dict[str, Any]]) -> dict[str, Any]:
    coverage_scores = [r["coverage_score"] for r in results]
    total_direct = sum(r["tier_counts"]["direct"] for r in results)
    total_adjacent = sum(r["tier_counts"]["adjacent"] for r in results)
    total_nr = sum(r["tier_counts"]["not_responsive"] for r in results)
    total_chunks = total_direct + total_adjacent + total_nr
    return {
        "avg_coverage": round(_avg(coverage_scores), 1),
        "direct_pct": round(_pct(total_direct, total_chunks), 1),
        "adjacent_pct": round(_pct(total_adjacent, total_chunks), 1),
        "not_responsive_pct": round(_pct(total_nr, total_chunks), 1),
        "total_judgements": len(results),
        "total_chunks": total_chunks,
    }


def generate_report(all_results: list[dict[str, Any]], output_dir: Path) -> None:
    """Generate markdown report and raw JSON from judge results."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Raw JSON
    (output_dir / "raw_results.json").write_text(
        json.dumps(all_results, indent=2, default=str),
        encoding="utf-8",
    )

    # Group by model
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in all_results:
        by_model[r["embedding_model"]].append(r)

    # Group by model + answer_mode
    by_model_mode: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        by_model_mode[r["embedding_model"]][r["answer_mode"]].append(r)

    # Group by question
    by_question: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        by_question[r["question"]][r["embedding_model"]].append(r)

    models = sorted(by_model.keys())
    lines: list[str] = []

    # Level 1: Per-model summary
    lines.append("# Embedding Model Eval Report\n")
    lines.append("## Model Summary\n")
    lines.append("| Model | Avg Coverage | Direct % | Adjacent % | Not Responsive % | Judgements |")
    lines.append("|-------|-------------|----------|-----------|-----------------|------------|")
    for model in models:
        stats = _model_stats(by_model[model])
        lines.append(
            f"| {model} | {stats['avg_coverage']} | "
            f"{stats['direct_pct']}% | {stats['adjacent_pct']}% | "
            f"{stats['not_responsive_pct']}% | {stats['total_judgements']} |"
        )
    lines.append("")

    # Level 2: By question type
    lines.append("## By Question Type\n")
    answer_modes = sorted({r["answer_mode"] for r in all_results})
    for mode in answer_modes:
        lines.append(f"### {mode}\n")
        lines.append("| Model | Avg Coverage | Direct % | Adjacent % | Not Responsive % |")
        lines.append("|-------|-------------|----------|-----------|-----------------|")
        for model in models:
            mode_results = by_model_mode[model].get(mode, [])
            if not mode_results:
                lines.append(f"| {model} | - | - | - | - |")
                continue
            stats = _model_stats(mode_results)
            lines.append(
                f"| {model} | {stats['avg_coverage']} | "
                f"{stats['direct_pct']}% | {stats['adjacent_pct']}% | "
                f"{stats['not_responsive_pct']}% |"
            )
        lines.append("")

    # Level 3: Per-question detail
    lines.append("## Per-Question Detail\n")
    for question, model_results in by_question.items():
        short_q = question[:100] + "..." if len(question) > 100 else question
        lines.append(f"### {short_q}\n")
        lines.append("| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |")
        lines.append("|-------|----------|--------|----------|-----------|------|")
        for model in models:
            results = model_results.get(model, [])
            if not results:
                lines.append(f"| {model} | - | - | - | - | - |")
                continue
            for r in results:
                div = r.get("division_acronym", "?")
                gaps = r.get("coverage_gaps", "none")
                short_gaps = gaps[:60] + "..." if len(gaps) > 60 else gaps
                tc = r["tier_counts"]
                lines.append(
                    f"| {model} [{div}] | {r['coverage_score']} | "
                    f"{tc['direct']} | {tc['adjacent']} | "
                    f"{tc['not_responsive']} | {short_gaps} |"
                )
        lines.append("")

    report_text = "\n".join(lines)
    (output_dir / "report.md").write_text(report_text, encoding="utf-8")
