"""Reduce stage: fold mapped Chunks for one Division into a Division-level answer."""

from __future__ import annotations

import re
import time
from typing import Any

from langgraph.types import Send

from app.models.query import NumberAnnotation, NumberAnnotationTarget
from app.services.llm_factory import create_chat_model, format_model_spec, resolve_model
from app.services.rag.annotations import (
    annotations_from_dicts,
    count_number_markers,
    figure_handle_prompt_context,
    prepare_figure_handle_context,
    render_figure_handle_answer,
    unmarked_figures,
)
from app.services.rag.context import RAGContext
from app.services.rag.llm_invocation import invoke_structured
from app.services.rag.relevance import (
    merge_relevance_counts,
    render_tiered_facts,
    summarize_relevance,
)
from app.services.rag.response import log_answer_budget
from app.services.rag.schemas import MarkedAnswer
from app.services.rag.state import DivisionAnswerState, MappedChunkState, RAGState
from app.services.rag_prompting import DEFAULT_ANSWER_MODE, build_reduce_prompt
from app.services.vector_store_service import division_acronym


_QUESTION_FACT_CUES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("amount", ("$", "appropriat", "provided", "funding")),
    ("availab", ("availab", "remain", "became", "october", "september")),
    ("date", ("availab", "october", "september", "through")),
    ("tranche", ("tranche", "previous", "earlier", "resciss", "advance")),
    ("amounts", ("resciss", "previous", "earlier", "became", "reimburse")),
    ("care", ("care", "medical", "treatment")),
    ("service", ("service", "program", "activity")),
    ("use", ("use", "purpose", "expense", "activity")),
)
_RECONCILIATION_BOUNDARY_CUES = (
    "transfer",
    "cap",
    "limitation",
    "not to exceed",
    "percent",
    "rescission",
    "set-aside",
    "set aside",
    "offsetting collection",
    "user fee",
)


def _prioritize_generation_facts(
    facts: list[dict[str, Any]],
    question: str,
) -> list[dict[str, Any]]:
    """Stably rank facts by the explicit components requested in the question."""
    question_text = question.lower()
    question_tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", question_text)
        if len(token) >= 4
    }

    def score(fact: dict[str, Any]) -> int:
        fact_text = str(fact.get("fact", "")).lower()
        fact_tokens = set(re.findall(r"[a-z0-9]+", fact_text))
        value = len(question_tokens & fact_tokens)
        for question_cue, fact_cues in _QUESTION_FACT_CUES:
            if question_cue in question_text and any(cue in fact_text for cue in fact_cues):
                value += 4
        if "amounts" in question_text or "tranche" in question_text:
            account_change_weights = (
                ("resciss", 24),
                ("previously appropriated", 12),
                ("earlier", 12),
                ("became available", 8),
                ("advance appropriat", 8),
                ("reimburse", 6),
            )
            value += sum(
                weight
                for term, weight in account_change_weights
                if term in fact_text
            )
        return value

    return sorted(facts, key=score, reverse=True)


def _label_generation_facts(
    facts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Add stable prompt-local ids so Reduce can audit Direct-fact coverage."""
    counters = {"direct": 0, "adjacent": 0}
    prefixes = {"direct": "D", "adjacent": "A"}
    labeled: list[dict[str, Any]] = []
    direct_ids: list[str] = []
    for fact in facts:
        tier = str(fact.get("responsiveness_tier", ""))
        copied = dict(fact)
        if tier in counters:
            counters[tier] += 1
            prompt_id = f"{prefixes[tier]}{counters[tier]}"
            copied["prompt_id"] = prompt_id
            if tier == "direct":
                direct_ids.append(prompt_id)
        labeled.append(copied)
    return labeled, direct_ids


def _required_fact_ids(
    facts: list[dict[str, Any]],
    *,
    answer_mode: str,
) -> list[str]:
    """Select facts Reduce must explicitly cover or justify excluding."""
    required: list[str] = []
    reconciliation = answer_mode == "reconciliation_breakdown"
    for fact in facts:
        prompt_id = str(fact.get("prompt_id", "") or "")
        if not prompt_id:
            continue
        tier = str(fact.get("responsiveness_tier", ""))
        fact_text = str(fact.get("fact", "")).lower()
        if tier == "direct" or (
            reconciliation
            and tier == "adjacent"
            and any(cue in fact_text for cue in _RECONCILIATION_BOUNDARY_CUES)
        ):
            required.append(prompt_id)
    return required


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

    relevance_facts = [
        fact
        for item in mapped_items
        for fact in item.get("relevance_facts", [])
        if isinstance(fact, dict)
    ]
    if relevance_facts:
        generation_facts = [
            fact
            for fact in relevance_facts
            if fact.get("responsiveness_tier") in {"direct", "adjacent"}
        ]
        generation_facts = _prioritize_generation_facts(
            generation_facts,
            state["question"],
        )
        generation_facts, _ = _label_generation_facts(generation_facts)
        required_fact_ids = _required_fact_ids(
            generation_facts,
            answer_mode=state.get("answer_mode", DEFAULT_ANSWER_MODE),
        )
        facts = render_tiered_facts(generation_facts) if generation_facts else ""
    else:
        # Compatibility for persisted/test mapped items created before
        # fact-level relevance metadata was introduced.
        facts = "\n\n".join(item["extracted_facts"] for item in mapped_items)
        required_fact_ids = []
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
        handle_context = prepare_figure_handle_context(facts, source_annotations)
        prompt = build_reduce_prompt(
            question=state["question"],
            division=division,
            division_acronym=division_acronym_value,
            answer_mode=state.get("answer_mode", DEFAULT_ANSWER_MODE),
            answer_mode_flags=state.get("answer_mode_flags", {}),
            annotation_context=figure_handle_prompt_context(handle_context),
            facts=handle_context.prompt_text,
            required_fact_ids=required_fact_ids,
        )
        marked = invoke_structured(
            llm,
            prompt,
            schema=MarkedAnswer,
            model_spec=reduce_model,
            stage="reduce",
            query_id=state.get("query_id", "unknown"),
            debug_log=ctx.debug_log,
        )
        covered_fact_ids = {
            fact_id for fact_id in marked.covered_fact_ids if fact_id in required_fact_ids
        }
        excluded_fact_ids = {
            fact_id for fact_id in marked.excluded_fact_ids if fact_id in required_fact_ids
        }
        missing_fact_ids = [
            fact_id
            for fact_id in required_fact_ids
            if fact_id not in covered_fact_ids and fact_id not in excluded_fact_ids
        ]
        ctx.debug_log(
            "reduce_fact_coverage query_id=%s division=%s required=%s covered=%s excluded=%s missing=%s",
            state.get("query_id", "unknown"),
            division_acronym_value,
            len(required_fact_ids),
            sorted(covered_fact_ids),
            sorted(excluded_fact_ids),
            missing_fact_ids,
        )
        proposed_derived_count = len(marked.derived_annotations)
        answer, derived = render_figure_handle_answer(
            marked=marked,
            context=handle_context,
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
