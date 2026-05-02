"""Number Annotation pipeline.

Builds Source-backed Figures from mapped chunk evidence, validates Derived
Figures proposed by reduce/synthesize against their input annotations and
displayed markdown, marks figures inline with hidden ``[[num:ID]]`` tokens,
and assembles the final response-shaped annotation list with deduplicated
``targets``.

All functions here are pure: they take state and a ``debug_log`` callable
where logging is needed, and return new values without touching service state.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Callable

from app.models.query import (
    DerivedNumberReference,
    NumberAnnotation,
    NumberAnnotationTarget,
    SourceNumberReference,
)
from app.services.rag.schemas import ProposedDerivedAnnotation, SourceNumberCandidate
from app.services.rag.state import (
    FIGURE_PATTERN,
    NUMBER_MARKER_PATTERN,
    RAGState,
    RetrievedChunkState,
)


_LABEL_MAX_LEN = 120
_LABEL_TRUNCATE_AT = 117
_ID_MAX_LEN = 80
_ID_TRUNCATE_AT = 68
_SCALE_MULTIPLIERS: dict[str, int] = {
    "thousand": 1_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
    "trillion": 1_000_000_000_000,
}


def count_number_markers(text: str) -> int:
    """Count hidden number markers in markdown text."""
    return len(NUMBER_MARKER_PATTERN.findall(text or ""))


def immediate_number_marker(text: str, figure_end: int) -> re.Match[str] | None:
    """Return a marker only when it belongs to the figure that just ended."""
    suffix = (text or "")[figure_end : figure_end + 80]
    return re.match(r"^[\s,.;:)\*_~`]*\[\[num:([A-Za-z0-9_-]+)\]\]", suffix)


def unmarked_figures(text: str, limit: int = 12) -> list[str]:
    """Return displayed dollar figures that are not immediately followed by a marker."""
    figures: list[str] = []
    for match in FIGURE_PATTERN.finditer(text or ""):
        if immediate_number_marker(text, match.end()):
            continue
        figures.append(match.group(0))
        if len(figures) >= limit:
            break
    return figures


def parse_dollar_figure(text: str) -> float | None:
    """Parse a displayed dollar figure into normalized dollars."""
    scale_words = "thousand|million|billion|trillion"
    match = re.search(
        rf"\$\s*([\d,]+(?:\.\d+)?)(?:\s*({scale_words}))?",
        text,
        re.IGNORECASE,
    )
    if not match:
        match = re.search(
            rf"\b(\d{{1,3}}(?:,\d{{3}})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*({scale_words})\b",
            text,
            re.IGNORECASE,
        )
    if not match:
        match = re.search(
            r"\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?)\b",
            text,
            re.IGNORECASE,
        )
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    scale = match.group(2) if match.lastindex and match.lastindex >= 2 else ""
    multiplier = _SCALE_MULTIPLIERS.get((scale or "").lower(), 1)
    return value * multiplier


def normalize_figure(figure: str) -> float | None:
    """Normalize a displayed dollar figure to dollars."""
    return parse_dollar_figure(figure)


def values_close(left: float, right: float) -> bool:
    """Compare normalized dollar values with a small display-rounding tolerance."""
    tolerance = max(1.0, abs(left) * 0.01)
    return abs(left - right) <= tolerance


def annotation_id(*parts: str) -> str:
    """Build a marker-safe deterministic annotation id."""
    raw = "_".join(parts).lower()
    safe = re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")
    if len(safe) <= _ID_MAX_LEN:
        return safe
    suffix = uuid.uuid5(uuid.NAMESPACE_URL, raw).hex[:10]
    return f"{safe[:_ID_TRUNCATE_AT].rstrip('_')}_{suffix}"


def source_label(extracted_facts: str, figure: str) -> str:
    """Build a short label for source-backed figure popovers from mapped facts."""
    for line in extracted_facts.splitlines():
        if figure in line:
            label = re.sub(r"\s+", " ", line).strip(" -*")
            return label[:_LABEL_TRUNCATE_AT].rstrip() + "..." if len(label) > _LABEL_MAX_LEN else label
    label = re.sub(r"\s+", " ", extracted_facts).strip(" -*")
    if not label:
        return "Source-backed figure"
    return label[:_LABEL_TRUNCATE_AT].rstrip() + "..." if len(label) > _LABEL_MAX_LEN else label


def fallback_source_number_candidates(extracted_facts: str) -> list[SourceNumberCandidate]:
    """Build source candidates from mapped facts when structured map output is unavailable."""
    candidates: list[SourceNumberCandidate] = []
    for match in FIGURE_PATTERN.finditer(extracted_facts):
        figure = match.group(0)
        value = normalize_figure(figure)
        if value is None:
            continue
        candidates.append(
            SourceNumberCandidate(
                figure=figure,
                value=value,
                label=source_label(extracted_facts, figure),
            )
        )
    return candidates


def source_number_annotations(
    chunk: RetrievedChunkState,
    extracted_facts: str,
    candidates: list[SourceNumberCandidate],
) -> list[NumberAnnotation]:
    """Build source-backed annotations from relevant mapped facts."""
    if not chunk["chunk_id"]:
        return []

    annotations: list[NumberAnnotation] = []
    seen_keys: set[tuple[str, str]] = set()
    source_candidates = candidates or fallback_source_number_candidates(extracted_facts)
    for index, candidate in enumerate(source_candidates, start=1):
        figure = candidate.figure.strip()
        value = candidate.value if candidate.value is not None else normalize_figure(figure)
        if value is None:
            continue
        if figure not in extracted_facts or figure not in chunk["content"]:
            continue

        label = candidate.label.strip() or source_label(extracted_facts, figure)
        seen_key = (figure.lower(), label.lower())
        if seen_key in seen_keys:
            continue
        seen_keys.add(seen_key)

        marker_id = annotation_id("src", chunk["division_acronym"], chunk["chunk_id"], str(index))
        annotations.append(
            NumberAnnotation(
                id=marker_id,
                kind="source",
                figure=figure,
                value=value,
                label=label,
                source=SourceNumberReference(chunk_id=chunk["chunk_id"]),
            )
        )
    return annotations


def mark_text_with_source_annotations(text: str, annotations: list[NumberAnnotation]) -> str:
    """Add hidden source markers to extracted fact text when figures match chunk evidence."""
    by_figure: dict[str, list[NumberAnnotation]] = {}
    for annotation in annotations:
        by_figure.setdefault(annotation.figure.lower(), []).append(annotation)

    used_by_figure: dict[str, int] = {}

    def replace(match: re.Match[str]) -> str:
        figure = match.group(0)
        if immediate_number_marker(text, match.end()):
            return figure
        candidates = by_figure.get(figure.lower(), [])
        if candidates:
            key = figure.lower()
            candidate_index = min(used_by_figure.get(key, 0), len(candidates) - 1)
            used_by_figure[key] = used_by_figure.get(key, 0) + 1
            return f"{figure} [[num:{candidates[candidate_index].id}]]"
        return figure

    return FIGURE_PATTERN.sub(replace, text)


def displayed_figure_for_marker(text: str, marker_id: str) -> str | None:
    """Find the displayed dollar figure directly associated with a marker."""
    marker_match = re.search(rf"\[\[num:{re.escape(marker_id)}\]\]", text or "")
    if not marker_match:
        return None

    prefix = (text or "")[: marker_match.start()]
    candidates = list(FIGURE_PATTERN.finditer(prefix))
    if not candidates:
        return None

    last_match = candidates[-1]
    between = prefix[last_match.end() :]
    if re.fullmatch(r"[\s,.;:)\*_~]*", between):
        return last_match.group(0)
    return None


def flatten_source_input_ids(
    input_ids: list[str],
    available_by_id: dict[str, NumberAnnotation],
) -> list[str]:
    """Flatten source and nested derived inputs into source annotation ids."""
    source_ids: list[str] = []
    seen_source_ids: set[str] = set()

    def visit(annotation_id_value: str, stack: set[str]) -> bool:
        if annotation_id_value in stack:
            return False
        annotation = available_by_id.get(annotation_id_value)
        if not annotation:
            return False

        if annotation.kind == "source":
            if not annotation.source or not annotation.source.chunk_id:
                return False
            if annotation.id not in seen_source_ids:
                seen_source_ids.add(annotation.id)
                source_ids.append(annotation.id)
            return True

        if annotation.kind == "derived" and annotation.derived and annotation.derived.source_input_ids:
            for source_id in annotation.derived.source_input_ids:
                source_annotation = available_by_id.get(source_id)
                if (
                    source_annotation
                    and source_annotation.kind == "source"
                    and source_annotation.source
                    and source_id not in seen_source_ids
                ):
                    seen_source_ids.add(source_id)
                    source_ids.append(source_id)
            return True

        child_ids = annotation.derived.input_ids if annotation.kind == "derived" and annotation.derived else []
        return all(visit(child_id, stack | {annotation_id_value}) for child_id in child_ids)

    return source_ids if all(visit(input_id, set()) for input_id in input_ids) else []


def annotations_from_dicts(annotations: Any) -> list[NumberAnnotation]:
    """Normalize annotation dicts/models carried through LangGraph reducers."""
    normalized: list[NumberAnnotation] = []
    for annotation in annotations or []:
        try:
            if isinstance(annotation, NumberAnnotation):
                normalized.append(annotation)
            elif isinstance(annotation, dict):
                normalized.append(NumberAnnotation.model_validate(annotation))
        except Exception:
            continue
    return normalized


def annotation_prompt_context(annotations: list[NumberAnnotation]) -> str:
    """Create compact annotation context for reduce/synthesis prompts."""
    if not annotations:
        return "None."
    lines = []
    for annotation in annotations:
        if annotation.kind == "source":
            chunk_id = annotation.source.chunk_id if annotation.source else "unknown"
            lines.append(
                f"- {annotation.id}: {annotation.figure} ({annotation.value:.0f}) "
                f"{annotation.label} chunk={chunk_id}"
            )
        else:
            input_ids = annotation.derived.input_ids if annotation.derived else []
            lines.append(
                f"- {annotation.id}: {annotation.figure} ({annotation.value:.0f}) "
                f"{annotation.label}; inputs={', '.join(input_ids)}"
            )
    return "\n".join(lines)


def validate_derived_annotations(
    *,
    proposed: list[ProposedDerivedAnnotation],
    target_answer: str,
    available: list[NumberAnnotation],
    target: NumberAnnotationTarget,
    debug_log: Callable[..., None],
    query_id: str = "unknown",
    stage: str = "unknown",
    target_label: str = "unknown",
) -> list[NumberAnnotation]:
    """Validate derived annotation proposals against markers, inputs, and arithmetic."""
    available_by_id = {annotation.id: annotation for annotation in available}
    accepted: list[NumberAnnotation] = []
    used_ids = set(available_by_id)
    rejection_counts: dict[str, int] = {}
    rejection_details: dict[str, list[dict[str, Any]]] = {}

    def reject(reason: str, proposal: ProposedDerivedAnnotation) -> None:
        rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
        rejection_details.setdefault(reason, [])
        if len(rejection_details[reason]) < 5:
            rejection_details[reason].append(
                {
                    "id": proposal.id,
                    "proposed_figure": proposal.proposed_figure,
                    "value": proposal.value,
                    "input_ids": proposal.input_ids,
                }
            )

    for proposal in proposed:
        if proposal.id in used_ids:
            reject("duplicate_id", proposal)
            continue
        if f"[[num:{proposal.id}]]" not in target_answer:
            reject("missing_marker", proposal)
            continue

        displayed_figure = displayed_figure_for_marker(target_answer, proposal.id)
        displayed_value = normalize_figure(displayed_figure) if displayed_figure else None
        if displayed_value is None:
            reject("missing_or_unparseable_displayed_marker_figure", proposal)
            continue

        source_input_ids = flatten_source_input_ids(proposal.input_ids, available_by_id)
        if not source_input_ids:
            reject("no_source_backed_inputs", proposal)
            continue

        input_total = sum(available_by_id[source_id].value for source_id in source_input_ids)
        proposed_value = proposal.value
        if not values_close(displayed_value, proposed_value):
            reject("displayed_proposed_value_mismatch", proposal)
            continue
        if not values_close(displayed_value, input_total):
            reject("input_sum_mismatch", proposal)
            continue

        accepted_annotation = NumberAnnotation(
            id=proposal.id,
            kind="derived",
            figure=displayed_figure,
            value=displayed_value,
            label=proposal.label,
            targets=[target],
            derived=DerivedNumberReference(
                equation=proposal.equation,
                rationale=proposal.rationale or None,
                input_ids=proposal.input_ids,
                source_input_ids=source_input_ids,
            ),
        )
        accepted.append(accepted_annotation)
        available_by_id[proposal.id] = accepted_annotation
        used_ids.add(proposal.id)

    if proposed or accepted or rejection_counts:
        debug_log(
            "derived_validation query_id=%s stage=%s target=%s proposed=%s accepted=%s rejected=%s "
            "rejected_details=%s available=%s available_source=%s available_derived=%s "
            "accepted_ids=%s accepted_figures=%s",
            query_id,
            stage,
            target_label,
            len(proposed),
            len(accepted),
            rejection_counts,
            rejection_details,
            len(available),
            sum(1 for annotation in available if annotation.kind == "source"),
            sum(1 for annotation in available if annotation.kind == "derived"),
            [annotation.id for annotation in accepted],
            [annotation.figure for annotation in accepted],
        )
    return accepted


def final_number_annotations(
    result: RAGState,
    *,
    debug_log: Callable[..., None],
) -> list[NumberAnnotation]:
    """Return de-duplicated annotations whose markers appear in returned markdown."""
    annotations = annotations_from_dicts(result.get("number_annotations", []))
    by_id = {annotation.id: annotation for annotation in annotations}
    final: list[NumberAnnotation] = []

    for annotation_id_value, annotation in by_id.items():
        targets: list[NumberAnnotationTarget] = []
        if f"[[num:{annotation_id_value}]]" in result.get("final_answer", ""):
            targets.append(NumberAnnotationTarget(scope="answer"))

        for division in result.get("division_answers", []):
            if f"[[num:{annotation_id_value}]]" in division.get("answer", ""):
                targets.append(
                    NumberAnnotationTarget(
                        scope="division",
                        division=division["division"],
                    )
                )

        if targets:
            updated = annotation.model_copy(update={"targets": targets})
            final.append(updated)

    answer = result.get("final_answer", "")
    division_answers = "\n\n".join(division.get("answer", "") for division in result.get("division_answers", []))
    debug_log(
        "response_annotations query_id=%s raw_annotations=%s unique_annotations=%s returned_annotations=%s "
        "returned_source=%s returned_derived=%s answer_markers=%s division_markers=%s "
        "unmarked_answer_figures=%s unmarked_division_figures=%s returned_ids=%s returned_figures=%s",
        result.get("query_id", "unknown"),
        len(annotations),
        len(by_id),
        len(final),
        sum(1 for annotation in final if annotation.kind == "source"),
        sum(1 for annotation in final if annotation.kind == "derived"),
        count_number_markers(answer),
        count_number_markers(division_answers),
        unmarked_figures(answer),
        unmarked_figures(division_answers),
        [annotation.id for annotation in final[:20]],
        [annotation.figure for annotation in final[:20]],
    )
    return final


__all__ = [
    "count_number_markers",
    "immediate_number_marker",
    "unmarked_figures",
    "parse_dollar_figure",
    "normalize_figure",
    "values_close",
    "annotation_id",
    "source_label",
    "fallback_source_number_candidates",
    "source_number_annotations",
    "mark_text_with_source_annotations",
    "displayed_figure_for_marker",
    "flatten_source_input_ids",
    "annotations_from_dicts",
    "annotation_prompt_context",
    "validate_derived_annotations",
    "final_number_annotations",
]
