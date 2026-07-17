"""Map stage: extract structured facts and UI summaries from one Chunk."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from langgraph.types import Send

from app.services.llm_factory import create_chat_model, resolve_model
from app.services.rag.annotations import (
    mark_text_with_source_annotations,
    source_number_annotations,
)
from app.services.rag.context import RAGContext
from app.services.rag.llm_invocation import invoke_structured, invoke_text
from app.services.rag.relevance import (
    normalize_mapped_fact_records,
    relevance_counts,
    render_tiered_facts,
)
from app.services.rag.schemas import MappedFacts
from app.services.rag.state import MappedChunkState, RAGState, RetrievedChunkState
from app.services.rag_prompting import DEFAULT_ANSWER_MODE, build_map_prompt


_SUMMARY_PROMPT_TEMPLATE = (
    "Write exactly one plain-English sentence for a source hover summary. "
    "Explain what useful evidence this chunk contains and why it matters for the question. "
    "Keep it under 35 words. Do not use bullets or introduce new facts.\n\n"
    "Question:\n{question}\n\n"
    "Source chunk:\n{chunk}"
)
_SNAPSHOT_PROMPT_TEMPLATE = (
    "Write exactly one plain-English sentence fragment under 14 words for a UI excerpt label. "
    "Mention the main agency, program, account, or dollar figure if present. "
    "Do not use bullets, clauses joined by semicolons, or introduce new facts.\n\n"
    "Question:\n{question}\n\n"
    "Source chunk:\n{chunk}"
)


def fan_out_chunks(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Provide a graph synchronization point before chunk mapping."""
    del state, ctx
    return {}


def send_chunks_to_map(state: RAGState, ctx: RAGContext) -> list[Send]:
    """Create LangGraph Send events that map every retrieved chunk independently."""
    del ctx
    return [
        Send(
            "map_chunk",
            {
                "question": state["question"],
                "query_id": state.get("query_id", "unknown"),
                "chunk": chunk,
                "thinking_speed": state.get("thinking_speed", "normal"),
                "answer_mode": state.get("answer_mode", DEFAULT_ANSWER_MODE),
                "answer_mode_flags": state.get("answer_mode_flags", {}),
            },
        )
        for chunk in state.get("retrieved_chunks", [])
    ]


def map_chunk(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Extract relevant facts and UI summaries from one retrieved chunk."""
    chunk: RetrievedChunkState = state["chunk"]  # type: ignore[typeddict-item]
    thinking_speed = state.get("thinking_speed", "normal")
    map_model = resolve_model(thinking_speed, "map")
    summary_model = resolve_model(thinking_speed, "summary")
    ctx.emit_progress(
        state,
        "mapping",
        "Reading retrieved chunks",
        division=chunk["division_acronym"],
    )
    map_llm = create_chat_model(map_model.model, "map", map_model.reasoning_effort)
    summary_llm = create_chat_model(summary_model.model, "summary", summary_model.reasoning_effort)
    question = state["question"]

    extraction_prompt = build_map_prompt(
        question=question,
        chunk_content=chunk["content"],
        division_acronym=chunk["division_acronym"],
        answer_mode=state.get("answer_mode", DEFAULT_ANSWER_MODE),
        answer_mode_flags=state.get("answer_mode_flags", {}),
    )
    summary_prompt = _SUMMARY_PROMPT_TEMPLATE.format(question=question, chunk=chunk["content"])
    snapshot_prompt = _SNAPSHOT_PROMPT_TEMPLATE.format(question=question, chunk=chunk["content"])

    query_id = state.get("query_id", "unknown")
    with ThreadPoolExecutor(max_workers=3) as executor:
        facts_future = executor.submit(
            invoke_structured,
            map_llm,
            extraction_prompt,
            schema=MappedFacts,
            model_spec=map_model,
            stage="map",
            query_id=query_id,
            debug_log=ctx.debug_log,
        )
        summary_future = executor.submit(
            invoke_text,
            summary_llm,
            summary_prompt,
            stage="summary",
            query_id=query_id,
            debug_log=ctx.debug_log,
        )
        snapshot_future = executor.submit(
            invoke_text,
            summary_llm,
            snapshot_prompt,
            stage="summary",
            query_id=query_id,
            debug_log=ctx.debug_log,
        )
        mapped_facts = facts_future.result()
        chunk_summary = summary_future.result()
        chunk_snapshot = snapshot_future.result()

    relevance_facts = normalize_mapped_fact_records(mapped_facts)
    direct_text = "\n".join(
        item["fact"] for item in relevance_facts if item["responsiveness_tier"] == "direct"
    )
    direct_candidates = [
        candidate
        for fact in mapped_facts.facts
        if fact.responsiveness_tier == "direct"
        for candidate in fact.source_numbers
    ] or mapped_facts.source_numbers
    annotations = source_number_annotations(chunk, direct_text, direct_candidates)
    for item in relevance_facts:
        if item["responsiveness_tier"] == "direct":
            item["fact"] = mark_text_with_source_annotations(item["fact"], annotations)
    extracted_facts = render_tiered_facts(relevance_facts)
    counts = relevance_counts(relevance_facts)

    mapped: MappedChunkState = {
        "chunk_id": chunk["chunk_id"],
        "division": chunk["division"],
        "division_acronym": chunk["division_acronym"],
        "extracted_facts": extracted_facts,
        "chunk_summary": chunk_summary,
        "chunk_snapshot": chunk_snapshot,
        "source_content": chunk["content"],
        "score": chunk.get("score"),
        "metadata": chunk.get("metadata", {}),
        "number_annotations": [
            annotation.model_dump(mode="json", exclude_none=True) for annotation in annotations
        ],
        "relevance_facts": relevance_facts,
        "relevance_counts": counts,
    }
    return {
        "mapped_chunks": [mapped],
        "number_annotations": [
            annotation.model_dump(mode="json", exclude_none=True) for annotation in annotations
        ],
        "relevance_metadata": [
            {
                "scope": "chunk",
                "chunk_id": chunk["chunk_id"],
                "division": chunk["division"],
                "division_acronym": chunk["division_acronym"],
                "counts": counts,
                "facts": relevance_facts,
            }
        ],
    }


__all__ = ["fan_out_chunks", "send_chunks_to_map", "map_chunk"]
