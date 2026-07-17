"""Deterministic Number Annotation checks for E2E evaluation results."""

from __future__ import annotations

import re
from typing import Any, Iterator

from app.models.query import NumberAnnotation
from app.services.rag.annotations import (
    flatten_source_input_ids,
    immediate_number_marker,
    normalize_figure,
    values_close,
)
from app.services.rag.state import FIGURE_PATTERN, NUMBER_MARKER_PATTERN


def _issue(code: str, scope: str, detail: str) -> dict[str, str]:
    return {"code": code, "scope": scope, "detail": detail}


def _markdown_fields(result: dict[str, Any]) -> Iterator[tuple[str, str]]:
    yield "answer", str(result.get("final_answer", "") or "")
    for index, division_answer in enumerate(result.get("division_answers", []) or []):
        division = (
            division_answer.get("division_acronym")
            or division_answer.get("division")
            or str(index)
        )
        yield f"division:{division}", str(division_answer.get("answer", "") or "")


def _figure_before_marker(text: str, marker_start: int) -> str | None:
    """Return the dollar figure directly associated with one marker occurrence."""
    prefix = text[:marker_start]
    candidates = list(FIGURE_PATTERN.finditer(prefix))
    if not candidates:
        return None
    last_match = candidates[-1]
    between = prefix[last_match.end() :]
    if re.fullmatch(r"[\s,.;:)\*_~`]*", between):
        return last_match.group(0)
    return None


def _chunk_contains_value(chunk: dict[str, Any], value: float) -> bool:
    for match in FIGURE_PATTERN.finditer(str(chunk.get("content", "") or "")):
        chunk_value = normalize_figure(match.group(0))
        if chunk_value is not None and values_close(chunk_value, value):
            return True
    return False


def evaluate_provenance(result: dict[str, Any]) -> dict[str, Any]:
    """Evaluate visible Number Annotation integrity without an LLM judge.

    The input is the response-shaped subset captured by the E2E runner. The
    returned dictionary is JSON-compatible so it can be stored directly in
    ``raw_results.json`` and rendered by the report generator.
    """
    issues: list[dict[str, str]] = []
    annotations_by_id: dict[str, NumberAnnotation] = {}

    for index, raw_annotation in enumerate(result.get("number_annotations", []) or []):
        try:
            annotation = (
                raw_annotation
                if isinstance(raw_annotation, NumberAnnotation)
                else NumberAnnotation.model_validate(raw_annotation)
            )
        except Exception as exc:
            summary = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
            issues.append(_issue("invalid_annotation", "annotations", f"index={index}: {summary}"))
            continue
        if annotation.id in annotations_by_id:
            issues.append(
                _issue("duplicate_annotation_id", "annotations", f"id={annotation.id}")
            )
            continue
        annotations_by_id[annotation.id] = annotation
        annotation_figure_value = normalize_figure(annotation.figure)
        if annotation_figure_value is None or not values_close(
            annotation_figure_value, annotation.value
        ):
            issues.append(
                _issue(
                    "annotation_figure_value_mismatch",
                    "annotations",
                    f"id={annotation.id} figure={annotation.figure} value={annotation.value:g}",
                )
            )

    marker_ids: list[str] = []
    answer_marker_count = 0
    division_marker_count = 0

    for scope, text in _markdown_fields(result):
        for figure_match in FIGURE_PATTERN.finditer(text):
            if immediate_number_marker(text, figure_match.end()) is None:
                issues.append(
                    _issue(
                        "unmarked_figure",
                        scope,
                        f"figure={figure_match.group(0)}",
                    )
                )

        markers = list(NUMBER_MARKER_PATTERN.finditer(text))
        if scope == "answer":
            answer_marker_count += len(markers)
        else:
            division_marker_count += len(markers)

        for marker_match in markers:
            marker_id = marker_match.group(1)
            marker_ids.append(marker_id)
            displayed_figure = _figure_before_marker(text, marker_match.start())
            if displayed_figure is None:
                issues.append(_issue("detached_marker", scope, f"id={marker_id}"))

            annotation = annotations_by_id.get(marker_id)
            if annotation is None:
                issues.append(_issue("unknown_marker", scope, f"id={marker_id}"))
                continue

            displayed_value = normalize_figure(displayed_figure or "")
            if displayed_value is not None and not values_close(displayed_value, annotation.value):
                issues.append(
                    _issue(
                        "marker_value_mismatch",
                        scope,
                        f"id={marker_id} displayed={displayed_figure} "
                        f"annotation={annotation.value:g}",
                    )
                )

    marker_id_set = set(marker_ids)
    for annotation_id in annotations_by_id:
        if annotation_id not in marker_id_set:
            issues.append(
                _issue("unused_annotation", "annotations", f"id={annotation_id}")
            )

    retrieved_by_id = {
        str(chunk.get("chunk_id")): chunk
        for chunk in result.get("retrieved_chunks", []) or []
        if chunk.get("chunk_id")
    }

    for annotation in annotations_by_id.values():
        if annotation.kind == "source":
            chunk_id = annotation.source.chunk_id if annotation.source else ""
            chunk = retrieved_by_id.get(chunk_id)
            if chunk is None:
                issues.append(
                    _issue(
                        "source_chunk_not_retrieved",
                        "annotations",
                        f"id={annotation.id} chunk_id={chunk_id}",
                    )
                )
            elif not _chunk_contains_value(chunk, annotation.value):
                issues.append(
                    _issue(
                        "source_value_not_in_chunk",
                        "annotations",
                        f"id={annotation.id} chunk_id={chunk_id} value={annotation.value:g}",
                    )
                )
            continue

        derived = annotation.derived
        if derived is None:
            continue
        if not derived.equation.strip():
            issues.append(
                _issue("derived_equation_missing", "annotations", f"id={annotation.id}")
            )
        if not derived.input_ids:
            issues.append(
                _issue("derived_inputs_missing", "annotations", f"id={annotation.id}")
            )
        for input_id in derived.input_ids:
            if input_id == annotation.id:
                issues.append(
                    _issue(
                        "derived_input_self_reference",
                        "annotations",
                        f"id={annotation.id}",
                    )
                )
            if input_id not in annotations_by_id:
                issues.append(
                    _issue(
                        "derived_input_unknown",
                        "annotations",
                        f"id={annotation.id} input_id={input_id}",
                    )
                )

        if not derived.source_input_ids:
            issues.append(
                _issue("derived_source_inputs_missing", "annotations", f"id={annotation.id}")
            )
            continue

        expected_source_input_ids = flatten_source_input_ids(
            derived.input_ids, annotations_by_id
        )
        if expected_source_input_ids and expected_source_input_ids != derived.source_input_ids:
            issues.append(
                _issue(
                    "derived_source_inputs_mismatch",
                    "annotations",
                    f"id={annotation.id} expected={expected_source_input_ids} "
                    f"actual={derived.source_input_ids}",
                )
            )

        source_inputs: list[NumberAnnotation] = []
        for source_input_id in derived.source_input_ids:
            source_annotation = annotations_by_id.get(source_input_id)
            if source_annotation is None:
                issues.append(
                    _issue(
                        "derived_source_input_unknown",
                        "annotations",
                        f"id={annotation.id} source_input_id={source_input_id}",
                    )
                )
            elif source_annotation.kind != "source":
                issues.append(
                    _issue(
                        "derived_source_input_not_source",
                        "annotations",
                        f"id={annotation.id} source_input_id={source_input_id}",
                    )
                )
            else:
                source_inputs.append(source_annotation)

        if len(source_inputs) == len(derived.source_input_ids):
            input_total = sum(source.value for source in source_inputs)
            if not values_close(input_total, annotation.value):
                issues.append(
                    _issue(
                        "derived_value_mismatch",
                        "annotations",
                        f"id={annotation.id} inputs={input_total:g} "
                        f"annotation={annotation.value:g}",
                    )
                )

    return {
        "passed": not issues,
        "answer_marker_count": answer_marker_count,
        "division_marker_count": division_marker_count,
        "annotation_count": len(annotations_by_id),
        "source_annotation_count": sum(
            1 for annotation in annotations_by_id.values() if annotation.kind == "source"
        ),
        "derived_annotation_count": sum(
            1 for annotation in annotations_by_id.values() if annotation.kind == "derived"
        ),
        "issues": issues,
    }


__all__ = ["evaluate_provenance"]
