"""Response shaping helpers for the public QueryResponse contract."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable

from app.models.query import (
    DebugDivisionQuery,
    DivisionResult,
    QueryResponse,
    SourceDocument,
)
from app.services.rag.annotations import final_number_annotations
from app.services.rag.state import MappedChunkState, RAGState


_BUDGET_WORDS_LIMIT = 900
_BUDGET_BULLETS_LIMIT = 14


def answer_budget_counts(text: str) -> dict[str, int]:
    """Return approximate word and bullet counts for generated answer budget logs."""
    return {
        "words": len(re.findall(r"\b\w+\b", text or "")),
        "bullets": len(re.findall(r"(?m)^\s*(?:[-*]|\d+\.)\s+", text or "")),
    }


def log_answer_budget(
    *,
    query_id: str,
    stage: str,
    label: str,
    text: str,
    debug_log: Callable[..., None],
) -> None:
    """Log answers that exceed broad-answer budget targets."""
    counts = answer_budget_counts(text)
    if counts["words"] > _BUDGET_WORDS_LIMIT or counts["bullets"] > _BUDGET_BULLETS_LIMIT:
        debug_log(
            "answer_budget query_id=%s stage=%s label=%s words=%s bullets=%s "
            "target_words<=900 target_bullets<=14",
            query_id,
            stage,
            label,
            counts["words"],
            counts["bullets"],
        )


def source_documents(
    result: RAGState,
    mapped_by_chunk: dict[str, MappedChunkState],
) -> list[SourceDocument]:
    """Build source document records from retrieved and mapped chunks."""
    return [
        SourceDocument(
            division=chunk["division"],
            division_acronym=chunk["division_acronym"],
            chunk_id=chunk["chunk_id"] or "",
            content_snippet=chunk["content"],
            chunk_summary=mapped_by_chunk.get(chunk["chunk_id"], {}).get("chunk_summary"),
            chunk_snapshot=mapped_by_chunk.get(chunk["chunk_id"], {}).get("chunk_snapshot"),
            confidence_score=None,
            metadata=chunk.get("metadata", {}),
        )
        for chunk in result.get("retrieved_chunks", [])
        if chunk["chunk_id"]
    ]


def debug_division_queries(result: RAGState) -> list[DebugDivisionQuery]:
    """Build debug records showing the retrieval query used for each division."""
    return [
        DebugDivisionQuery(
            division=item["division"],
            division_acronym=item["division_acronym"],
            query=item["query"],
        )
        for item in result.get("division_queries", [])
    ]


def to_response(
    result: RAGState,
    processing_time: float,
    query_id: str,
    *,
    debug_log: Callable[..., None],
    debug_enabled: bool,
) -> QueryResponse:
    """Convert final graph state into the public QueryResponse model.

    Args:
        result: Final graph state returned by LangGraph.
        processing_time: Total query processing time in seconds.
        query_id: Query identifier to expose in the API response.
        debug_log: Callable used by ``final_number_annotations`` for trace logging.
        debug_enabled: Whether to include debug-only fields in the response.

    Returns:
        QueryResponse containing the final answer, divisions, sources, and metadata.
    """
    mapped_by_chunk: dict[str, Any] = {
        chunk["chunk_id"]: chunk
        for chunk in result.get("mapped_chunks", [])
        if chunk["chunk_id"]
    }
    sources = (
        source_documents(result, mapped_by_chunk)
        if result.get("include_sources")
        else None
    )

    return QueryResponse(
        answer=result.get("final_answer", ""),
        processing_time=processing_time,
        selected_divisions=result.get("selected_divisions", []),
        division_results=[
            DivisionResult(
                division=item["division"],
                division_acronym=item["division_acronym"],
                chunks_retrieved=item["chunks_retrieved"],
                answer=item["answer"],
                source_chunk_ids=item["source_chunk_ids"],
            )
            for item in result.get("division_answers", [])
        ],
        sources=sources,
        number_annotations=final_number_annotations(result, debug_log=debug_log),
        debug_division_queries=debug_division_queries(result) if debug_enabled else None,
        query_id=query_id,
        timestamp=datetime.utcnow(),
        thinking_speed=result.get("thinking_speed"),
        model_used=result.get("model_used"),
    )


__all__ = [
    "answer_budget_counts",
    "log_answer_budget",
    "source_documents",
    "debug_division_queries",
    "to_response",
]
