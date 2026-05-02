"""LangGraph state types and shared regex constants for the RAG pipeline."""

from __future__ import annotations

import operator
import re
from typing import Annotated, Any

from typing_extensions import TypedDict

from app.core.config import get_settings
from app.models.query import QueryRequest


FIGURE_PATTERN = re.compile(
    r"\$(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:\s*(?:thousand|million|billion|trillion))?",
    re.IGNORECASE,
)
NUMBER_MARKER_PATTERN = re.compile(r"\[\[num:([A-Za-z0-9_-]+)\]\]")


class DivisionQueryState(TypedDict):
    division: str
    division_acronym: str
    query: str


class RetrievedChunkState(TypedDict):
    chunk_id: str | None
    division: str
    division_acronym: str
    content: str
    chunk_summary: str | None
    score: float | None
    metadata: dict[str, Any]


class MappedChunkState(TypedDict):
    chunk_id: str | None
    division: str
    division_acronym: str
    extracted_facts: str
    chunk_summary: str
    chunk_snapshot: str
    source_content: str
    score: float | None
    metadata: dict[str, Any]
    number_annotations: list[dict[str, Any]]
    relevance_facts: list[dict[str, Any]]
    relevance_counts: dict[str, int]


class DivisionAnswerState(TypedDict):
    division: str
    division_acronym: str
    answer: str
    source_chunk_ids: list[str]
    chunks_retrieved: int
    number_annotations: list[dict[str, Any]]
    relevance_counts: dict[str, int]
    relevance_summary: dict[str, Any]


class RAGState(TypedDict, total=False):
    query_id: str
    question: str
    thinking_speed: str
    max_results: int
    include_sources: bool
    divisions_filter: list[str] | None
    model_used: str
    vector_store_id: str | None
    vector_store_root: str | None
    vector_store_embedding_model: str | None
    answer_mode: str
    answer_mode_flags: dict[str, Any]
    answer_mode_reason: str
    selected_divisions: list[str]
    division_queries: list[DivisionQueryState]
    retrieved_chunks: Annotated[list[RetrievedChunkState], operator.add]
    mapped_chunks: Annotated[list[MappedChunkState], operator.add]
    division_answers: Annotated[list[DivisionAnswerState], operator.add]
    number_annotations: Annotated[list[dict[str, Any]], operator.add]
    relevance_metadata: Annotated[list[dict[str, Any]], operator.add]
    final_answer: str


def retrieval_k_for_request(request: QueryRequest) -> int:
    """Return the number of chunks to retrieve per selected division.

    Args:
        request: Validated query request containing an optional max_results value.

    Returns:
        Chunk count per division, falling back to the configured default.
    """
    return request.max_results or get_settings().default_results_per_division
