"""Reduce stage: fold mapped Chunks for one Division into a Division-level answer."""

from __future__ import annotations

import time
from typing import Any

from langgraph.types import Send

from app.models.query import NumberAnnotation, NumberAnnotationTarget
from app.services.llm_factory import create_chat_model, format_model_spec, resolve_model
from app.services.rag.annotations import (
    annotation_prompt_context,
    annotations_from_dicts,
    count_number_markers,
    unmarked_figures,
    validate_derived_annotations,
)
from app.services.rag.context import RAGContext
from app.services.rag.llm_invocation import invoke_structured_or_text
from app.services.rag.relevance import merge_relevance_counts, summarize_relevance
from app.services.rag.response import log_answer_budget
from app.services.rag.schemas import MarkedAnswer
from app.services.rag.state import DivisionAnswerState, MappedChunkState, RAGState
from app.services.rag_prompting import DEFAULT_ANSWER_MODE, build_reduce_prompt
from app.services.vector_store_service import division_acronym


def fan_out_reduce_divisions(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Provide a graph synchronization point before division reduction."""
    del state, ctx
    return {}


def send_divisions_to_reduce(state: RAGState, ctx: RAGContext) -> list[Send]:
    """Group mapped chunks by division and create reduction Send events."""
    by_division: dict[str, list[MappedChunkState]] = {}
    retrieved_counts: dict[str, int] = {}

    for chunk in state.get("retrieved_chunks", []):
        retrieved_counts[chunk["division"]] = retrieved_counts.get(chunk["division"], 0) + 1

    for mapped in state.get("mapped_chunks", []):
        by_division.setdefault(mapped["division"], []).append(mapped)

    divisions = state.get("selected_divisions", [])
    ctx.emit_progress(
        state,
        "reducing",
        "Simplifying division answers",
        divisions=[division_acronym(division) for division in divisions],
    )

    return [
        Send(
            "reduce_division",
            {
                "question": state["question"],
                "query_id": state.get("query_id", "unknown"),
                "division": division,
                "division_acronym": division_acronym(division),
                "mapped_items": by_division.get(division, []),
                "chunks_retrieved": retrieved_counts.get(division, 0),
                "thinking_speed": state.get("thinking_speed", "normal"),
                "answer_mode": state.get("answer_mode", DEFAULT_ANSWER_MODE),
                "answer_mode_flags": state.get("answer_mode_flags", {}),
            },
        )
        for division in state.get("selected_divisions", [])
    ]


def reduce_division(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Synthesize mapped chunk facts into one division-level answer."""
    start_time = time.time()
    division = state["division"]  # type: ignore[typeddict-item]
    division_acronym_value = state["division_acronym"]  # type: ignore[typeddict-item]
    mapped_items: list[MappedChunkState] = state.get("mapped_items", [])  # type: ignore[assignment]
    chunks_retrieved = state.get("chunks_retrieved", 0)
    reduce_model = resolve_model(state.get("thinking_speed", "normal"), "reduce")
    ctx.debug_log(
        "reduce_start query_id=%s division=%s model=%s mapped_items=%s chunks_retrieved=%s",
        state.get("query_id", "unknown"),
        division_acronym_value,
        format_model_spec(reduce_model),
        len(mapped_items),
        chunks_retrieved,
    )
    ctx.emit_progress(
        state,
        "reducing",
        "Simplifying division answer",
        division=division_acronym_value,
        divisions=[division_acronym_value],
        model=format_model_spec(reduce_model),
    )
    llm = create_chat_model(reduce_model.model, "reduce", reduce_model.reasoning_effort)

    facts = "\n\n".join(item["extracted_facts"] for item in mapped_items)
    relevance_facts = [
        fact
        for item in mapped_items
        for fact in item.get("relevance_facts", [])
        if isinstance(fact, dict)
    ]
    counts = merge_relevance_counts(
        [item.get("relevance_counts", {}) for item in mapped_items]
    )
    summary = summarize_relevance(relevance_facts)
    ctx.debug_log(
        "reduce_relevance query_id=%s division=%s counts=%s direct_examples=%s adjacent_examples=%s",
        state.get("query_id", "unknown"),
        division_acronym_value,
        counts,
        len(summary.get("direct_examples", [])),
        len(summary.get("adjacent_examples", [])),
    )
    source_annotations = annotations_from_dicts(
        annotation
        for item in mapped_items
        for annotation in item.get("number_annotations", [])
    )
    unmarked_fact_figures = unmarked_figures(facts)
    if unmarked_fact_figures:
        ctx.debug_log(
            "reduce_annotation_input_gaps query_id=%s division=%s mapped_items=%s source_annotations=%s "
            "source_markers_in_facts=%s unmarked_fact_figures=%s",
            state.get("query_id", "unknown"),
            division_acronym_value,
            len(mapped_items),
            len(source_annotations),
            count_number_markers(facts),
            unmarked_fact_figures,
        )
    if not facts.strip():
        answer = "No relevant facts found for this division."
        derived: list[NumberAnnotation] = []
        proposed_derived_count = 0
    else:
        prompt = build_reduce_prompt(
            question=state["question"],
            division=division,
            division_acronym=division_acronym_value,
            answer_mode=state.get("answer_mode", DEFAULT_ANSWER_MODE),
            answer_mode_flags=state.get("answer_mode_flags", {}),
            annotation_context=annotation_prompt_context(source_annotations),
            facts=facts,
        )
        marked = invoke_structured_or_text(
            llm,
            prompt,
            schema=MarkedAnswer,
            fallback=lambda text: MarkedAnswer(answer=text),
            stage="reduce",
            query_id=state.get("query_id", "unknown"),
            debug_log=ctx.debug_log,
        )
        answer = marked.answer
        proposed_derived_count = len(marked.derived_annotations)
        derived = validate_derived_annotations(
            proposed=marked.derived_annotations,
            target_answer=answer,
            available=source_annotations,
            target=NumberAnnotationTarget(scope="division", division=division),
            debug_log=ctx.debug_log,
            query_id=state.get("query_id", "unknown"),
            stage="reduce",
            target_label=division_acronym_value,
        )

    division_answer: DivisionAnswerState = {
        "division": division,
        "division_acronym": division_acronym_value,
        "answer": answer,
        "source_chunk_ids": [item["chunk_id"] for item in mapped_items if item["chunk_id"]],
        "chunks_retrieved": chunks_retrieved,
        "number_annotations": [
            annotation.model_dump(mode="json", exclude_none=True) for annotation in derived
        ],
        "relevance_counts": counts,
        "relevance_summary": summary,
    }
    log_answer_budget(
        query_id=state.get("query_id", "unknown"),
        stage="reduce",
        label=division_acronym_value,
        text=answer,
        debug_log=ctx.debug_log,
    )
    ctx.debug_log(
        "reduce_done query_id=%s division=%s model=%s mapped_items=%s input_chars=%s duration=%.2fs answer_chars=%s",
        state.get("query_id", "unknown"),
        division_acronym_value,
        format_model_spec(reduce_model),
        len(mapped_items),
        len(facts),
        time.time() - start_time,
        len(answer),
    )
    unmarked_answer_figures = unmarked_figures(answer)
    if unmarked_answer_figures or proposed_derived_count or derived:
        ctx.debug_log(
            "reduce_annotations_output query_id=%s division=%s proposed_derived=%s accepted_derived=%s "
            "answer_markers=%s unmarked_answer_figures=%s accepted_ids=%s accepted_figures=%s",
            state.get("query_id", "unknown"),
            division_acronym_value,
            proposed_derived_count,
            len(derived),
            count_number_markers(answer),
            unmarked_answer_figures,
            [annotation.id for annotation in derived],
            [annotation.figure for annotation in derived],
        )
    return {
        "division_answers": [division_answer],
        "number_annotations": [
            annotation.model_dump(mode="json", exclude_none=True) for annotation in derived
        ],
        "relevance_metadata": [
            {
                "scope": "division",
                "division": division,
                "division_acronym": division_acronym_value,
                "counts": counts,
                "summary": summary,
            }
        ],
    }


__all__ = ["fan_out_reduce_divisions", "send_divisions_to_reduce", "reduce_division"]
