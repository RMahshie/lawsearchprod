"""Synthesize stage: combine Division answers into the final response."""

from __future__ import annotations

import time
from typing import Any

from app.models.query import NumberAnnotationTarget
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
from app.services.rag.response import log_answer_budget
from app.services.rag.schemas import MarkedAnswer
from app.services.rag.state import RAGState
from app.services.rag_prompting import DEFAULT_ANSWER_MODE, build_synthesis_prompt


def synthesize_final(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Combine division-level answers into the final response text."""
    start_time = time.time()
    division_answers = state.get("division_answers", [])
    if not division_answers:
        existing_answer = state.get("final_answer")
        if existing_answer:
            ctx.debug_log(
                "synthesize_skip query_id=%s reason=existing_final_answer answer_chars=%s",
                state.get("query_id", "unknown"),
                len(existing_answer),
            )
            return {"final_answer": existing_answer}
        ctx.debug_log(
            "synthesize_skip query_id=%s reason=no_division_answers",
            state.get("query_id", "unknown"),
        )
        return {"final_answer": "No answers found."}

    if len(division_answers) == 1:
        answer = division_answers[0]["answer"]
        ctx.debug_log(
            "synthesize_skip query_id=%s reason=single_division division=%s answer_chars=%s",
            state.get("query_id", "unknown"),
            division_answers[0]["division_acronym"],
            len(answer),
        )
        return {"final_answer": answer}

    synthesize_model = resolve_model(state.get("thinking_speed", "normal"), "synthesize")
    ctx.emit_progress(
        state,
        "synthesizing",
        "Combining final result",
        divisions=[item["division_acronym"] for item in division_answers],
        model=format_model_spec(synthesize_model),
    )
    ctx.debug_log(
        "synthesize_start query_id=%s model=%s division_answers=%s",
        state.get("query_id", "unknown"),
        format_model_spec(synthesize_model),
        len(division_answers),
    )
    llm = create_chat_model(
        synthesize_model.model,
        "synthesize",
        synthesize_model.reasoning_effort,
    )
    context = "\n\n".join(
        f"## {item['division']} [{item['division_acronym']}]\n"
        f"Relevance counts: {item.get('relevance_counts', {})}\n"
        f"Relevance summary: {item.get('relevance_summary', {})}\n"
        f"{item['answer']}"
        for item in division_answers
    )
    available_annotations = annotations_from_dicts(state.get("number_annotations", []))
    ctx.debug_log(
        "synthesize_annotations_input query_id=%s available_annotations=%s available_source=%s available_derived=%s "
        "division_answer_markers=%s division_unmarked_figures=%s annotation_ids=%s",
        state.get("query_id", "unknown"),
        len(available_annotations),
        sum(1 for annotation in available_annotations if annotation.kind == "source"),
        sum(1 for annotation in available_annotations if annotation.kind == "derived"),
        count_number_markers(context),
        unmarked_figures(context),
        [annotation.id for annotation in available_annotations[:16]],
    )
    prompt = build_synthesis_prompt(
        question=state["question"],
        answer_mode=state.get("answer_mode", DEFAULT_ANSWER_MODE),
        answer_mode_flags=state.get("answer_mode_flags", {}),
        annotation_context=annotation_prompt_context(available_annotations),
        division_context=context,
    )
    marked = invoke_structured_or_text(
        llm,
        prompt,
        schema=MarkedAnswer,
        model_spec=synthesize_model,
        fallback=lambda text: MarkedAnswer(answer=text),
        stage="synthesize",
        query_id=state.get("query_id", "unknown"),
        debug_log=ctx.debug_log,
    )
    final_answer = marked.answer
    log_answer_budget(
        query_id=state.get("query_id", "unknown"),
        stage="synthesize",
        label="answer",
        text=final_answer,
        debug_log=ctx.debug_log,
    )
    derived = validate_derived_annotations(
        proposed=marked.derived_annotations,
        target_answer=final_answer,
        available=available_annotations,
        target=NumberAnnotationTarget(scope="answer"),
        debug_log=ctx.debug_log,
        query_id=state.get("query_id", "unknown"),
        stage="synthesize",
        target_label="answer",
    )
    ctx.debug_log(
        "synthesize_done query_id=%s model=%s division_answers=%s input_chars=%s duration=%.2fs answer_chars=%s",
        state.get("query_id", "unknown"),
        format_model_spec(synthesize_model),
        len(division_answers),
        len(context),
        time.time() - start_time,
        len(final_answer),
    )
    unmarked_answer_figures = unmarked_figures(final_answer)
    if unmarked_answer_figures or marked.derived_annotations or derived:
        ctx.debug_log(
            "synthesize_annotations_output query_id=%s proposed_derived=%s accepted_derived=%s "
            "answer_markers=%s unmarked_answer_figures=%s accepted_ids=%s accepted_figures=%s",
            state.get("query_id", "unknown"),
            len(marked.derived_annotations),
            len(derived),
            count_number_markers(final_answer),
            unmarked_answer_figures,
            [annotation.id for annotation in derived],
            [annotation.figure for annotation in derived],
        )
    return {
        "final_answer": final_answer,
        "number_annotations": [
            annotation.model_dump(mode="json", exclude_none=True) for annotation in derived
        ],
    }


__all__ = ["synthesize_final"]
