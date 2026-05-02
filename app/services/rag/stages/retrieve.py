"""Retrieve stage: pull top-k Chunks per selected Division from Chroma."""

from __future__ import annotations

import time
from typing import Any

from langgraph.types import Send

from app.services.rag.context import RAGContext
from app.services.rag.state import RAGState
from app.services.rag_prompting import DEFAULT_ANSWER_MODE
from app.services.vector_store_service import division_acronym


def fan_out_divisions(state: RAGState, ctx: RAGContext) -> list[Send]:
    """Create LangGraph Send events that retrieve chunks for each selected division.

    The ``ctx`` argument is unused here but kept for parity with other stages and
    so the graph builder can pass it through unconditionally.
    """
    del ctx  # not needed; retrieval Sends are pure state transformations.
    division_queries = state.get("division_queries") or [
        {
            "division": division,
            "division_acronym": division_acronym(division),
            "query": state["question"],
        }
        for division in state.get("selected_divisions", [])
    ]
    return [
        Send(
            "retrieve_division",
            {
                "question": state["question"],
                "query_id": state.get("query_id", "unknown"),
                "division": item["division"],
                "retrieval_query": item["query"],
                "max_results": state["max_results"],
                "vector_store_id": state.get("vector_store_id"),
                "vector_store_root": state.get("vector_store_root"),
                "vector_store_embedding_model": state.get("vector_store_embedding_model"),
                "answer_mode": state.get("answer_mode", DEFAULT_ANSWER_MODE),
                "answer_mode_flags": state.get("answer_mode_flags", {}),
            },
        )
        for item in division_queries
    ]


def retrieve_division(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Retrieve relevant source chunks for one division from the active vector store."""
    start_time = time.time()
    division = state["division"]  # type: ignore[typeddict-item]
    ctx.emit_progress(
        state,
        "retrieving",
        "Searching source text",
        division=division_acronym(division),
    )
    retrieval_query = state.get("retrieval_query", state["question"])  # type: ignore[typeddict-item]
    chunks = ctx.vectorstores.retrieve(
        question=retrieval_query,
        division=division,
        k=state["max_results"],
        vectorstore_root=state.get("vector_store_root"),
        embedding_model=state.get("vector_store_embedding_model"),
    )
    ctx.debug_log(
        "retrieve query_id=%s division=%s requested_k=%s returned=%s duration=%.2fs query_chars=%s",
        state.get("query_id", "unknown"),
        division_acronym(division),
        state["max_results"],
        len(chunks),
        time.time() - start_time,
        len(state.get("retrieval_query", state["question"])),  # type: ignore[typeddict-item]
    )
    return {"retrieved_chunks": chunks}


__all__ = ["fan_out_divisions", "retrieve_division"]
