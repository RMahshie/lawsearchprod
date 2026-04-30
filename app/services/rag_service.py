"""LangGraph RAG orchestration for LawSearch AI."""

from __future__ import annotations

import logging
import operator
import os
import re
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Lock
from typing import Annotated, Any, Callable, Literal, Optional

# In local development, Chroma may need the pysqlite3 shim. Docker uses system sqlite.
if os.getenv("ENVIRONMENT") != "production" and not os.path.exists("/.dockerenv"):
    try:
        import pysqlite3  # type: ignore[import-not-found]

        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        pass

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import TypedDict

from app.core.config import FY2026_INCOMPATIBLE_QUESTION_ANSWER, get_settings
from app.db.models import VectorStore
from app.db.session import SessionLocal, database_available
from app.models.query import (
    DebugDivisionQuery,
    DerivedNumberReference,
    DivisionResult,
    IngestResponse,
    NumberAnnotation,
    NumberAnnotationTarget,
    QueryRequest,
    QueryResponse,
    SourceNumberReference,
    SourceDocument,
)
from app.services.ingestion_service import IngestionService
from app.services.llm_factory import create_chat_model, describe_model_strategy, format_model_spec, resolve_model
from app.services.rag_prompting import (
    DEFAULT_ANSWER_MODE,
    build_map_prompt,
    build_reduce_prompt,
    build_synthesis_prompt,
    normalize_answer_mode,
)
from app.services.storage_registry import (
    create_vector_store_record,
    ensure_storage_ready,
    get_active_vector_store,
    mark_vector_store_failed,
    mark_vector_store_ready,
    save_query_response,
    vector_store_path,
)
from app.services.vector_store_service import VectorStoreService, division_acronym

logger = logging.getLogger(__name__)
INCOMPATIBLE_QUESTION_ANSWER = FY2026_INCOMPATIBLE_QUESTION_ANSWER


class AnswerModeFlags(BaseModel):
    """Safety flags selected with the route decision."""

    mixed_financial_types: bool = False


class RouteDecision(BaseModel):
    """Structured routing response."""

    divisions: list[str] = Field(default_factory=list)
    answer_mode: Literal[
        "direct_account_amount",
        "broad_topic_total",
        "funding_mechanism_no_amount",
        "reconciliation_breakdown",
        "general_summary",
    ] = DEFAULT_ANSWER_MODE
    answer_mode_flags: AnswerModeFlags = Field(default_factory=AnswerModeFlags)
    answer_mode_reason: str = ""


class DivisionQueryDecision(BaseModel):
    """Structured per-division retrieval query response."""

    division: str
    query: str


class DivisionQueryPlan(BaseModel):
    """Structured query rewrite response."""

    division_queries: list[DivisionQueryDecision] = Field(default_factory=list)


class ProposedDerivedAnnotation(BaseModel):
    """LLM-proposed derived figure provenance before deterministic validation."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    proposed_figure: str = Field(
        alias="figure",
        description="Model-proposed figure text. The displayed figure is read from the answer marker context.",
    )
    value: float
    label: str
    equation: str
    rationale: str = ""
    input_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_value(cls, data):
        """Accept current annotation proposals that still use normalized_value."""
        if isinstance(data, dict) and "value" not in data and "normalized_value" in data:
            data = dict(data)
            data["value"] = data.get("normalized_value")
        return data


class MarkedAnswer(BaseModel):
    """Structured answer text plus proposed derived number annotations."""

    answer: str
    derived_annotations: list[ProposedDerivedAnnotation] = Field(default_factory=list)


class SourceNumberCandidate(BaseModel):
    """LLM-proposed source-backed figure extracted from one mapped chunk."""

    figure: str
    value: float | None = None
    label: str


class MappedFact(BaseModel):
    """One mapped fact with scope responsiveness metadata."""

    fact: str
    responsiveness_tier: Literal["direct", "adjacent", "not_responsive"] = "direct"
    reason: str = ""
    source_numbers: list[SourceNumberCandidate] = Field(default_factory=list)


class MappedFacts(BaseModel):
    """Structured map output with facts and relevant source-backed numbers."""

    extracted_facts: str = ""
    facts: list[MappedFact] = Field(default_factory=list)
    source_numbers: list[SourceNumberCandidate] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_fact_objects(self):
        """Keep legacy extracted_facts/source_numbers output compatible with tiered facts."""
        if not self.facts and self.extracted_facts.strip() and self.extracted_facts.strip() != "- No relevant facts found.":
            self.facts = [
                MappedFact(
                    fact=line.strip(),
                    responsiveness_tier="direct",
                    source_numbers=self.source_numbers,
                )
                for line in self.extracted_facts.splitlines()
                if line.strip()
            ]
        if not self.extracted_facts.strip() and self.facts:
            self.extracted_facts = "\n".join(fact.fact for fact in self.facts)
        return self


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


FIGURE_PATTERN = re.compile(
    r"\$(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:\s*(?:thousand|million|billion|trillion))?",
    re.IGNORECASE,
)
NUMBER_MARKER_PATTERN = re.compile(r"\[\[num:([A-Za-z0-9_-]+)\]\]")


def retrieval_k_for_request(request: QueryRequest) -> int:
    """Return the number of chunks to retrieve per selected division.

    Args:
        request: Validated query request containing an optional max_results value.

    Returns:
        Chunk count per division, falling back to the configured default.
    """
    return request.max_results or get_settings().default_results_per_division


class RAGService:
    """Coordinates routing, retrieval, mapping, reduction, and ingestion."""

    def __init__(self):
        """Initialize RAG dependencies, progress callback storage, and the compiled graph.

        Args:
            None.

        Returns:
            None.
        """
        self.settings = get_settings()
        ensure_storage_ready()
        self.vectorstores = VectorStoreService()
        self.settings.embedding_model = self.vectorstores.embedding_model
        self.ingestion = IngestionService()
        self._progress_callbacks: dict[str, Callable[[dict[str, Any]], None]] = {}
        self._progress_lock = Lock()
        self._graph = self._build_graph()

    def _build_graph(self):
        """Build and compile the LangGraph workflow used for every query.

        Args:
            None.

        Returns:
            A compiled LangGraph application that transforms RAGState into final query state.
        """
        builder = StateGraph(RAGState)
        builder.add_node("route_divisions", self._route_divisions)
        builder.add_node("rewrite_division_queries", self._rewrite_division_queries)
        builder.add_node("retrieve_division", self._retrieve_division)
        builder.add_node("fan_out_chunks", self._fan_out_chunks)
        builder.add_node("map_chunk", self._map_chunk)
        builder.add_node("fan_out_reduce_divisions", self._fan_out_reduce_divisions)
        builder.add_node("reduce_division", self._reduce_division)
        builder.add_node("synthesize_final", self._synthesize_final)

        builder.add_edge(START, "route_divisions")
        builder.add_edge("route_divisions", "rewrite_division_queries")
        builder.add_conditional_edges(
            "rewrite_division_queries",
            self._fan_out_divisions,
            ["retrieve_division"],
        )
        builder.add_edge("retrieve_division", "fan_out_chunks")
        builder.add_conditional_edges(
            "fan_out_chunks",
            self._send_chunks_to_map,
            ["map_chunk"],
        )
        builder.add_edge("map_chunk", "fan_out_reduce_divisions")
        builder.add_conditional_edges(
            "fan_out_reduce_divisions",
            self._send_divisions_to_reduce,
            ["reduce_division"],
        )
        builder.add_edge("reduce_division", "synthesize_final")
        builder.add_edge("synthesize_final", END)
        return builder.compile()

    async def process_query(
        self,
        request: QueryRequest,
        query_id: Optional[str] = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> QueryResponse:
        """Process one query through routing, retrieval, mapping, reduction, and response persistence.

        Args:
            request: Validated query request from the API layer.
            query_id: Optional externally generated query identifier.
            progress_callback: Optional callback that receives streaming progress events.

        Returns:
            Structured query response with answer, divisions, sources, timing, and metadata.
        """
        start_time = time.time()
        query_id = query_id or f"query_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        thinking_speed = request.thinking_speed or "normal"
        model_used = describe_model_strategy(thinking_speed)
        if progress_callback:
            with self._progress_lock:
                self._progress_callbacks[query_id] = progress_callback

        active_store_id = None
        active_store_root = str(self.settings.vectorstore_dir)
        active_embedding_model = self.vectorstores.embedding_model
        if database_available() and SessionLocal is not None:
            try:
                with SessionLocal() as db:
                    active_store = get_active_vector_store(db)
                    if active_store:
                        active_store_id = active_store.id
                        active_store_root = str(vector_store_path(active_store))
                        active_embedding_model = active_store.embedding_model_id
            except Exception as exc:
                logger.warning("Storage registry unavailable; using configured Chroma store: %s", exc)

        state: RAGState = {
            "query_id": query_id,
            "question": request.question,
            "thinking_speed": thinking_speed,
            "max_results": retrieval_k_for_request(request),
            "include_sources": True,
            "divisions_filter": request.divisions_filter,
            "model_used": model_used,
            "vector_store_id": active_store_id,
            "vector_store_root": active_store_root,
            "vector_store_embedding_model": active_embedding_model,
            "answer_mode": DEFAULT_ANSWER_MODE,
            "answer_mode_flags": {"mixed_financial_types": False},
            "answer_mode_reason": "",
            "selected_divisions": [],
            "division_queries": [],
            "retrieved_chunks": [],
            "mapped_chunks": [],
            "division_answers": [],
            "number_annotations": [],
            "relevance_metadata": [],
            "final_answer": "",
        }
        self._debug_log(
            "query_start query_id=%s speed=%s model=%s max_results=%s include_sources=%s "
            "filter_count=%s question_chars=%s active_store_id=%s active_store_root=%s active_embedding_model=%s",
            query_id,
            thinking_speed,
            model_used,
            state["max_results"],
            state["include_sources"],
            len(request.divisions_filter or []),
            len(request.question),
            active_store_id,
            active_store_root,
            active_embedding_model,
        )
        self._emit_progress(query_id, "start", "Starting query", model=model_used)

        try:
            result = self._graph.invoke(state, config={"recursion_limit": 50})
        except Exception as exc:
            processing_time = time.time() - start_time
            logger.error("Query %s failed after %.2fs: %s", query_id, processing_time, exc, exc_info=True)
            if progress_callback:
                with self._progress_lock:
                    self._progress_callbacks.pop(query_id, None)
            raise Exception(f"RAG processing failed: {exc}") from exc

        processing_time = time.time() - start_time
        self._debug_log(
            "query_done query_id=%s duration=%.2fs selected_divisions=%s retrieved_chunks=%s "
            "mapped_chunks=%s division_answers=%s answer_mode=%s flags=%s",
            query_id,
            processing_time,
            len(result.get("selected_divisions", [])),
            len(result.get("retrieved_chunks", [])),
            len(result.get("mapped_chunks", [])),
            len(result.get("division_answers", [])),
            result.get("answer_mode"),
            result.get("answer_mode_flags"),
        )
        self._emit_progress(query_id, "done", "Done")
        if progress_callback:
            with self._progress_lock:
                self._progress_callbacks.pop(query_id, None)
        response = self._to_response(result, processing_time, query_id)
        if database_available() and SessionLocal is not None:
            try:
                with SessionLocal() as db:
                    vector_store = db.get(VectorStore, result.get("vector_store_id")) if result.get("vector_store_id") else None
                    save_query_response(
                        db,
                        response=response,
                        question=request.question,
                        vector_store=vector_store,
                        answer_mode=result.get("answer_mode"),
                        answer_mode_flags=result.get("answer_mode_flags"),
                        answer_mode_reason=result.get("answer_mode_reason"),
                        relevance_metadata=result.get("relevance_metadata"),
                    )
                    db.commit()
            except Exception as exc:
                logger.warning("Query result was not persisted: %s", exc)
        return response

    def _route_divisions(self, state: RAGState) -> dict[str, Any]:
        """Select which appropriations divisions should be searched for the query.

        Args:
            state: Current graph state containing the question and optional division filter.

        Returns:
            Partial state update with selected_divisions.
        """
        start_time = time.time()
        self._emit_progress(state, "routing", "Finding relevant divisions")
        requested_filter = state.get("divisions_filter")
        settings = getattr(self, "settings", get_settings())
        valid_divisions = list(settings.subcommittee_stores.keys())
        routing_model = resolve_model(state.get("thinking_speed", "normal"), "routing")
        routing_llm = create_chat_model(
            routing_model.model,
            "routing",
            routing_model.reasoning_effort,
        ).with_structured_output(RouteDecision)
        allowed_divisions = "\n".join(
            f"- {division}: {settings.routing_aliases.get(division, '')}"
            for division in valid_divisions
        )
        route_messages = [
            SystemMessage(
                content=(
                    "Select the relevant appropriations divisions and classify the answer style for this question. "
                    "Return only exact FY2026 division names from the allowed list. "
                    "Use the aliases only as routing hints, never as returned labels. "
                    "Set answer_mode to one of: direct_account_amount, broad_topic_total, "
                    "funding_mechanism_no_amount, reconciliation_breakdown, general_summary. "
                    "If the best mode is ambiguous, use broad_topic_total. "
                    "Set answer_mode_flags.mixed_financial_types=true when relevant figures may include "
                    "non-comparable financial types such as grants, loan authority, subsidy costs, user fees, "
                    "transfers, rescissions, caps, limitations, or set-asides. "
                    "Keep answer_mode_reason short."
                )
            ),
            HumanMessage(
                content=(
                    f"Allowed FY2026 divisions and routing hints:\n{allowed_divisions}\n\n"
                    f"Question: {state['question']}"
                )
            ),
        ]
        decision = self._invoke_with_retry(
            lambda: routing_llm.invoke(route_messages),
            stage="route",
            query_id=state.get("query_id", "unknown"),
        )
        answer_mode_update = self._answer_mode_update(decision)
        if requested_filter:
            self._debug_log(
                "route query_id=%s source=filter model=%s duration=%.2fs selected=%s answer_mode=%s flags=%s reason=%s",
                state.get("query_id", "unknown"),
                format_model_spec(routing_model),
                time.time() - start_time,
                len(requested_filter),
                answer_mode_update["answer_mode"],
                answer_mode_update["answer_mode_flags"],
                answer_mode_update["answer_mode_reason"],
            )
            return {"selected_divisions": requested_filter, **answer_mode_update}

        selected = [division for division in decision.divisions if division in settings.subcommittee_stores]
        if not selected:
            logger.info("Router returned no valid FY2026 divisions; ending as incompatible question")
            self._debug_log(
                "route query_id=%s source=llm model=%s duration=%.2fs selected=0 incompatible=true "
                "answer_mode=%s flags=%s reason=%s raw_divisions=%s",
                state.get("query_id", "unknown"),
                format_model_spec(routing_model),
                time.time() - start_time,
                answer_mode_update["answer_mode"],
                answer_mode_update["answer_mode_flags"],
                answer_mode_update["answer_mode_reason"],
                decision.divisions,
            )
            return {
                "selected_divisions": [],
                "final_answer": INCOMPATIBLE_QUESTION_ANSWER,
                **answer_mode_update,
            }
        self._debug_log(
            "route query_id=%s source=llm model=%s duration=%.2fs selected=%s divisions=%s "
            "answer_mode=%s flags=%s reason=%s",
            state.get("query_id", "unknown"),
            format_model_spec(routing_model),
            time.time() - start_time,
            len(selected),
            [division_acronym(division) for division in selected],
            answer_mode_update["answer_mode"],
            answer_mode_update["answer_mode_flags"],
            answer_mode_update["answer_mode_reason"],
        )
        return {"selected_divisions": selected, **answer_mode_update}

    def _answer_mode_update(self, decision: Any) -> dict[str, Any]:
        """Normalize route-classifier answer-mode metadata for graph state."""
        raw_mode = getattr(decision, "answer_mode", DEFAULT_ANSWER_MODE)
        flags = getattr(decision, "answer_mode_flags", None)
        if isinstance(flags, AnswerModeFlags):
            flags_dict = flags.model_dump()
        elif isinstance(flags, dict):
            flags_dict = {"mixed_financial_types": bool(flags.get("mixed_financial_types"))}
        else:
            flags_dict = {
                "mixed_financial_types": bool(getattr(flags, "mixed_financial_types", False)),
            }
        return {
            "answer_mode": normalize_answer_mode(raw_mode),
            "answer_mode_flags": flags_dict,
            "answer_mode_reason": str(getattr(decision, "answer_mode_reason", "") or "").strip(),
        }

    def _rewrite_division_queries(self, state: RAGState) -> dict[str, Any]:
        """Rewrite the original question into division-specific retrieval queries.

        Args:
            state: Current graph state containing the original question and selected divisions.

        Returns:
            Partial state update with per-division retrieval query decisions.
        """
        start_time = time.time()
        selected_divisions = state.get("selected_divisions", [])
        fallback_queries = [
            {
                "division": division,
                "division_acronym": division_acronym(division),
                "query": state["question"],
            }
            for division in selected_divisions
        ]
        if not selected_divisions:
            return {"division_queries": []}

        rewrite_model = resolve_model("quick", "routing")
        self._emit_progress(
            state,
            "rewriting",
            "Tailoring division search questions",
            divisions=[division_acronym(division) for division in selected_divisions],
            model=format_model_spec(rewrite_model),
        )

        try:
            rewrite_llm = create_chat_model(
                rewrite_model.model,
                "division_query_rewrite",
                rewrite_model.reasoning_effort,
            ).with_structured_output(DivisionQueryPlan)
            allowed_divisions = "\n- ".join(selected_divisions)
            rewrite_messages = [
                SystemMessage(
                    content=(
                        "Create one targeted retrieval query for each selected appropriations division. "
                        "Keep the user's intent, but only include entities, programs, agencies, or terms "
                        "likely relevant to that division. Do not force unrelated entities into every query. "
                        "Return exact division names from the selected list."
                    )
                ),
                HumanMessage(
                    content=(
                        f"Selected divisions:\n- {allowed_divisions}\n\n"
                        f"Original question:\n{state['question']}"
                    )
                ),
            ]
            plan = self._invoke_with_retry(
                lambda: rewrite_llm.invoke(rewrite_messages),
                stage="rewrite",
                query_id=state.get("query_id", "unknown"),
            )
            by_division = {
                item.division: item.query.strip()
                for item in plan.division_queries
                if item.division in selected_divisions and item.query.strip()
            }
            division_queries = [
                {
                    "division": division,
                    "division_acronym": division_acronym(division),
                    "query": by_division.get(division, state["question"]),
                }
                for division in selected_divisions
            ]
            self._debug_log(
                "rewrite query_id=%s model=%s duration=%.2fs divisions=%s rewritten=%s",
                state.get("query_id", "unknown"),
                format_model_spec(rewrite_model),
                time.time() - start_time,
                [division_acronym(division) for division in selected_divisions],
                len(by_division),
            )
            return {"division_queries": division_queries}
        except Exception as exc:
            logger.warning("Division query rewrite failed; using original question: %s", exc)
            self._debug_log(
                "rewrite_fallback query_id=%s model=%s duration=%.2fs divisions=%s",
                state.get("query_id", "unknown"),
                format_model_spec(rewrite_model),
                time.time() - start_time,
                [division_acronym(division) for division in selected_divisions],
            )
            return {"division_queries": fallback_queries}

    def _fan_out_divisions(self, state: RAGState) -> list[Send]:
        """Create LangGraph send events that retrieve chunks for each selected division.

        Args:
            state: Current graph state containing selected divisions and rewritten queries.

        Returns:
            Send commands targeting the retrieve_division node.
        """
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

    def _retrieve_division(self, state: RAGState) -> dict[str, Any]:
        """Retrieve relevant source chunks for one division from the active vector store.

        Args:
            state: Per-division graph state containing division, query, vector store, and k.

        Returns:
            Partial state update containing retrieved_chunks.
        """
        start_time = time.time()
        division = state["division"]  # type: ignore[typeddict-item]
        self._emit_progress(
            state,
            "retrieving",
            "Searching source text",
            division=division_acronym(division),
        )
        retrieval_query = state.get("retrieval_query", state["question"])  # type: ignore[typeddict-item]
        chunks = self.vectorstores.retrieve(
            question=retrieval_query,
            division=division,
            k=state["max_results"],
            vectorstore_root=state.get("vector_store_root"),
            embedding_model=state.get("vector_store_embedding_model"),
        )
        self._debug_log(
            "retrieve query_id=%s division=%s requested_k=%s returned=%s duration=%.2fs query_chars=%s",
            state.get("query_id", "unknown"),
            division_acronym(division),
            state["max_results"],
            len(chunks),
            time.time() - start_time,
            len(state.get("retrieval_query", state["question"])),  # type: ignore[typeddict-item]
        )
        return {"retrieved_chunks": chunks}

    def _fan_out_chunks(self, state: RAGState) -> dict[str, Any]:
        """Provide a graph synchronization point before chunk mapping.

        Args:
            state: Current graph state after retrieval.

        Returns:
            Empty state update because fan-out is handled by _send_chunks_to_map.
        """
        return {}

    def _send_chunks_to_map(self, state: RAGState) -> list[Send]:
        """Create LangGraph send events that map every retrieved chunk independently.

        Args:
            state: Current graph state containing retrieved chunks.

        Returns:
            Send commands targeting the map_chunk node.
        """
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

    def _map_chunk(self, state: RAGState) -> dict[str, Any]:
        """Extract relevant facts and UI summaries from one retrieved chunk.

        Args:
            state: Per-chunk graph state containing question, chunk, and thinking speed.

        Returns:
            Partial state update containing one mapped chunk.
        """
        start_time = time.time()
        chunk: RetrievedChunkState = state["chunk"]  # type: ignore[typeddict-item]
        thinking_speed = state.get("thinking_speed", "normal")
        map_model = resolve_model(thinking_speed, "map")
        summary_model = resolve_model(thinking_speed, "summary")
        self._emit_progress(
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
        summary_prompt = (
            "Write exactly one plain-English sentence for a source hover summary. "
            "Explain what useful evidence this chunk contains and why it matters for the question. "
            "Keep it under 35 words. Do not use bullets or introduce new facts.\n\n"
            f"Question:\n{question}\n\n"
            f"Source chunk:\n{chunk['content']}"
        )
        snapshot_prompt = (
            "Write exactly one plain-English sentence fragment under 14 words for a UI excerpt label. "
            "Mention the main agency, program, account, or dollar figure if present. "
            "Do not use bullets, clauses joined by semicolons, or introduce new facts.\n\n"
            f"Question:\n{question}\n\n"
            f"Source chunk:\n{chunk['content']}"
        )

        with ThreadPoolExecutor(max_workers=3) as executor:
            query_id = state.get("query_id", "unknown")
            facts_future = executor.submit(
                self._invoke_mapped_facts,
                map_llm,
                extraction_prompt,
                stage="map",
                query_id=query_id,
            )
            summary_future = executor.submit(
                self._invoke_text,
                summary_llm,
                summary_prompt,
                stage="summary",
                query_id=query_id,
            )
            snapshot_future = executor.submit(
                self._invoke_text,
                summary_llm,
                snapshot_prompt,
                stage="summary",
                query_id=query_id,
            )
            mapped_facts = facts_future.result()
            chunk_summary = summary_future.result()
            chunk_snapshot = snapshot_future.result()

        relevance_facts = self._normalize_mapped_fact_records(mapped_facts)
        direct_text = "\n".join(item["fact"] for item in relevance_facts if item["responsiveness_tier"] == "direct")
        direct_candidates = [
            candidate
            for fact in mapped_facts.facts
            if fact.responsiveness_tier == "direct"
            for candidate in fact.source_numbers
        ] or mapped_facts.source_numbers
        number_annotations = self._source_number_annotations(chunk, direct_text, direct_candidates)
        for item in relevance_facts:
            if item["responsiveness_tier"] == "direct":
                item["fact"] = self._mark_text_with_source_annotations(item["fact"], number_annotations)
        extracted_facts = self._render_tiered_facts(relevance_facts)
        relevance_counts = self._relevance_counts(relevance_facts)
        marker_count = self._count_number_markers(extracted_facts)
        unmarked_figures = self._unmarked_figures(extracted_facts)

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
            "number_annotations": [annotation.model_dump(mode="json", exclude_none=True) for annotation in number_annotations],
            "relevance_facts": relevance_facts,
            "relevance_counts": relevance_counts,
        }
        self._debug_log(
            "map query_id=%s chunk_id=%s division=%s map_model=%s summary_model=%s duration=%.2fs "
            "facts_chars=%s summary_chars=%s snapshot_chars=%s relevance_counts=%s",
            state.get("query_id", "unknown"),
            chunk["chunk_id"],
            chunk["division_acronym"],
            format_model_spec(map_model),
            format_model_spec(summary_model),
            time.time() - start_time,
            len(extracted_facts),
            len(chunk_summary),
            len(chunk_snapshot),
            relevance_counts,
        )
        if unmarked_figures:
            self._debug_log(
                "map_annotation_gaps query_id=%s chunk_id=%s division=%s structured_candidates=%s "
                "source_annotations=%s markers_in_facts=%s unmarked_figures=%s annotation_figures=%s",
                state.get("query_id", "unknown"),
                chunk["chunk_id"],
                chunk["division_acronym"],
                len(mapped_facts.source_numbers),
                len(number_annotations),
                marker_count,
                unmarked_figures,
                [annotation.figure for annotation in number_annotations[:8]],
            )
        return {
            "mapped_chunks": [mapped],
            "number_annotations": [annotation.model_dump(mode="json", exclude_none=True) for annotation in number_annotations],
            "relevance_metadata": [
                {
                    "scope": "chunk",
                    "chunk_id": chunk["chunk_id"],
                    "division": chunk["division"],
                    "division_acronym": chunk["division_acronym"],
                    "counts": relevance_counts,
                    "facts": relevance_facts,
                }
            ],
        }

    def _fan_out_reduce_divisions(self, state: RAGState) -> dict[str, Any]:
        """Provide a graph synchronization point before division reduction.

        Args:
            state: Current graph state after chunk mapping.

        Returns:
            Empty state update because fan-out is handled by _send_divisions_to_reduce.
        """
        return {}

    def _send_divisions_to_reduce(self, state: RAGState) -> list[Send]:
        """Group mapped chunks by division and create reduction send events.

        Args:
            state: Current graph state containing retrieved and mapped chunks.

        Returns:
            Send commands targeting the reduce_division node.
        """
        by_division: dict[str, list[MappedChunkState]] = {}
        retrieved_counts: dict[str, int] = {}

        for chunk in state.get("retrieved_chunks", []):
            retrieved_counts[chunk["division"]] = retrieved_counts.get(chunk["division"], 0) + 1

        for mapped in state.get("mapped_chunks", []):
            by_division.setdefault(mapped["division"], []).append(mapped)

        divisions = state.get("selected_divisions", [])
        self._emit_progress(
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

    def _reduce_division(self, state: RAGState) -> dict[str, Any]:
        """Synthesize mapped chunk facts into one division-level answer.

        Args:
            state: Per-division graph state containing mapped items and retrieval counts.

        Returns:
            Partial state update containing one division answer.
        """
        start_time = time.time()
        division = state["division"]  # type: ignore[typeddict-item]
        mapped_items: list[MappedChunkState] = state.get("mapped_items", [])  # type: ignore[assignment]
        chunks_retrieved = state.get("chunks_retrieved", 0)
        reduce_model = resolve_model(
            state.get("thinking_speed", "normal"),
            "reduce",
        )
        self._debug_log(
            "reduce_start query_id=%s division=%s model=%s mapped_items=%s chunks_retrieved=%s",
            state.get("query_id", "unknown"),
            state["division_acronym"],  # type: ignore[typeddict-item]
            format_model_spec(reduce_model),
            len(mapped_items),
            chunks_retrieved,
        )
        self._emit_progress(
            state,
            "reducing",
            "Simplifying division answer",
            division=state["division_acronym"],  # type: ignore[typeddict-item]
            divisions=[state["division_acronym"]],  # type: ignore[typeddict-item]
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
        relevance_counts = self._merge_relevance_counts(
            [item.get("relevance_counts", {}) for item in mapped_items]
        )
        relevance_summary = self._summarize_relevance(relevance_facts)
        self._debug_log(
            "reduce_relevance query_id=%s division=%s counts=%s direct_examples=%s adjacent_examples=%s",
            state.get("query_id", "unknown"),
            state["division_acronym"],  # type: ignore[typeddict-item]
            relevance_counts,
            len(relevance_summary.get("direct_examples", [])),
            len(relevance_summary.get("adjacent_examples", [])),
        )
        source_annotations = self._annotations_from_dicts(
            annotation
            for item in mapped_items
            for annotation in item.get("number_annotations", [])
        )
        unmarked_fact_figures = self._unmarked_figures(facts)
        if unmarked_fact_figures:
            self._debug_log(
                "reduce_annotation_input_gaps query_id=%s division=%s mapped_items=%s source_annotations=%s "
                "source_markers_in_facts=%s unmarked_fact_figures=%s",
                state.get("query_id", "unknown"),
                state["division_acronym"],  # type: ignore[typeddict-item]
                len(mapped_items),
                len(source_annotations),
                self._count_number_markers(facts),
                unmarked_fact_figures,
            )
        if not facts.strip():
            answer = "No relevant facts found for this division."
            derived_annotations: list[NumberAnnotation] = []
            proposed_derived_count = 0
        else:
            prompt = build_reduce_prompt(
                question=state["question"],
                division=division,
                division_acronym=state["division_acronym"],  # type: ignore[typeddict-item]
                answer_mode=state.get("answer_mode", DEFAULT_ANSWER_MODE),
                answer_mode_flags=state.get("answer_mode_flags", {}),
                annotation_context=self._annotation_prompt_context(source_annotations),
                facts=facts,
            )
            marked = self._invoke_marked_answer(
                llm,
                prompt,
                stage="reduce",
                query_id=state.get("query_id", "unknown"),
            )
            answer = marked.answer
            proposed_derived_count = len(marked.derived_annotations)
            derived_annotations = self._validate_derived_annotations(
                proposed=marked.derived_annotations,
                target_answer=answer,
                available=source_annotations,
                target=NumberAnnotationTarget(
                    scope="division",
                    division=division,
                ),
                query_id=state.get("query_id", "unknown"),
                stage="reduce",
                target_label=state["division_acronym"],  # type: ignore[typeddict-item]
            )

        division_answer: DivisionAnswerState = {
            "division": division,
            "division_acronym": state["division_acronym"],  # type: ignore[typeddict-item]
            "answer": answer,
            "source_chunk_ids": [item["chunk_id"] for item in mapped_items if item["chunk_id"]],
            "chunks_retrieved": chunks_retrieved,
            "number_annotations": [annotation.model_dump(mode="json", exclude_none=True) for annotation in derived_annotations],
            "relevance_counts": relevance_counts,
            "relevance_summary": relevance_summary,
        }
        self._log_answer_budget(
            query_id=state.get("query_id", "unknown"),
            stage="reduce",
            label=state["division_acronym"],  # type: ignore[typeddict-item]
            text=answer,
        )
        self._debug_log(
            "reduce_done query_id=%s division=%s model=%s mapped_items=%s input_chars=%s duration=%.2fs answer_chars=%s",
            state.get("query_id", "unknown"),
            state["division_acronym"],  # type: ignore[typeddict-item]
            format_model_spec(reduce_model),
            len(mapped_items),
            len(facts),
            time.time() - start_time,
            len(answer),
        )
        unmarked_answer_figures = self._unmarked_figures(answer)
        if unmarked_answer_figures or proposed_derived_count or derived_annotations:
            self._debug_log(
                "reduce_annotations_output query_id=%s division=%s proposed_derived=%s accepted_derived=%s "
                "answer_markers=%s unmarked_answer_figures=%s accepted_ids=%s accepted_figures=%s",
                state.get("query_id", "unknown"),
                state["division_acronym"],  # type: ignore[typeddict-item]
                proposed_derived_count,
                len(derived_annotations),
                self._count_number_markers(answer),
                unmarked_answer_figures,
                [annotation.id for annotation in derived_annotations],
                [annotation.figure for annotation in derived_annotations],
            )
        return {
            "division_answers": [division_answer],
            "number_annotations": [annotation.model_dump(mode="json", exclude_none=True) for annotation in derived_annotations],
            "relevance_metadata": [
                {
                    "scope": "division",
                    "division": division,
                    "division_acronym": state["division_acronym"],  # type: ignore[typeddict-item]
                    "counts": relevance_counts,
                    "summary": relevance_summary,
                }
            ],
        }

    def _synthesize_final(self, state: RAGState) -> dict[str, Any]:
        """Combine division-level answers into the final response text.

        Args:
            state: Current graph state containing all division answers.

        Returns:
            Partial state update containing final_answer.
        """
        start_time = time.time()
        division_answers = state.get("division_answers", [])
        if not division_answers:
            existing_answer = state.get("final_answer")
            if existing_answer:
                self._debug_log(
                    "synthesize_skip query_id=%s reason=existing_final_answer answer_chars=%s",
                    state.get("query_id", "unknown"),
                    len(existing_answer),
                )
                return {"final_answer": existing_answer}
            self._debug_log(
                "synthesize_skip query_id=%s reason=no_division_answers",
                state.get("query_id", "unknown"),
            )
            return {"final_answer": "No answers found."}

        if len(division_answers) == 1:
            answer = division_answers[0]["answer"]
            self._debug_log(
                "synthesize_skip query_id=%s reason=single_division division=%s answer_chars=%s",
                state.get("query_id", "unknown"),
                division_answers[0]["division_acronym"],
                len(answer),
            )
            return {"final_answer": answer}

        synthesize_model = resolve_model(
            state.get("thinking_speed", "normal"),
            "synthesize",
        )
        self._emit_progress(
            state,
            "synthesizing",
            "Combining final result",
            divisions=[item["division_acronym"] for item in division_answers],
            model=format_model_spec(synthesize_model),
        )
        self._debug_log(
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
        available_annotations = self._annotations_from_dicts(state.get("number_annotations", []))
        self._debug_log(
            "synthesize_annotations_input query_id=%s available_annotations=%s available_source=%s available_derived=%s "
            "division_answer_markers=%s division_unmarked_figures=%s annotation_ids=%s",
            state.get("query_id", "unknown"),
            len(available_annotations),
            sum(1 for annotation in available_annotations if annotation.kind == "source"),
            sum(1 for annotation in available_annotations if annotation.kind == "derived"),
            self._count_number_markers(context),
            self._unmarked_figures(context),
            [annotation.id for annotation in available_annotations[:16]],
        )
        prompt = build_synthesis_prompt(
            question=state["question"],
            answer_mode=state.get("answer_mode", DEFAULT_ANSWER_MODE),
            answer_mode_flags=state.get("answer_mode_flags", {}),
            annotation_context=self._annotation_prompt_context(available_annotations),
            division_context=context,
        )
        marked = self._invoke_marked_answer(
            llm,
            prompt,
            stage="synthesize",
            query_id=state.get("query_id", "unknown"),
        )
        final_answer = marked.answer
        self._log_answer_budget(
            query_id=state.get("query_id", "unknown"),
            stage="synthesize",
            label="answer",
            text=final_answer,
        )
        derived_annotations = self._validate_derived_annotations(
            proposed=marked.derived_annotations,
            target_answer=final_answer,
            available=available_annotations,
            target=NumberAnnotationTarget(scope="answer"),
            query_id=state.get("query_id", "unknown"),
            stage="synthesize",
            target_label="answer",
        )
        self._debug_log(
            "synthesize_done query_id=%s model=%s division_answers=%s input_chars=%s duration=%.2fs answer_chars=%s",
            state.get("query_id", "unknown"),
            format_model_spec(synthesize_model),
            len(division_answers),
            len(context),
            time.time() - start_time,
            len(final_answer),
        )
        unmarked_answer_figures = self._unmarked_figures(final_answer)
        if unmarked_answer_figures or marked.derived_annotations or derived_annotations:
            self._debug_log(
                "synthesize_annotations_output query_id=%s proposed_derived=%s accepted_derived=%s "
                "answer_markers=%s unmarked_answer_figures=%s accepted_ids=%s accepted_figures=%s",
                state.get("query_id", "unknown"),
                len(marked.derived_annotations),
                len(derived_annotations),
                self._count_number_markers(final_answer),
                unmarked_answer_figures,
                [annotation.id for annotation in derived_annotations],
                [annotation.figure for annotation in derived_annotations],
            )
        return {
            "final_answer": final_answer,
            "number_annotations": [annotation.model_dump(mode="json", exclude_none=True) for annotation in derived_annotations],
        }

    def _invoke_text(self, llm: Any, prompt: str, *, stage: str, query_id: str) -> str:
        """Invoke an LLM and normalize its response content to plain text.

        Args:
            llm: Chat model or compatible object with an invoke method.
            prompt: Prompt string to send to the model.
            stage: Pipeline stage name used for retry/debug logging.
            query_id: Query identifier used for retry/debug logging.

        Returns:
            Stripped text content from the model response.
        """
        response = self._invoke_with_retry(
            lambda: llm.invoke(prompt),
            stage=stage,
            query_id=query_id,
        )
        content = getattr(response, "content", response)
        if isinstance(content, list):
            return "\n".join(str(block) for block in content)
        return str(content).strip()

    def _invoke_with_retry(self, invoke_fn: Callable[[], Any], *, stage: str, query_id: str) -> Any:
        """Invoke a callable once and retry once for retryable LLM failures.

        Args:
            invoke_fn: Zero-argument callable that performs the model request.
            stage: Pipeline stage name used for debug logging.
            query_id: Query identifier used for debug logging.

        Returns:
            Result returned by invoke_fn.
        """
        try:
            return invoke_fn()
        except Exception as exc:
            if not self._is_retryable_llm_error(exc):
                raise

            self._debug_log(
                "retry query_id=%s stage=%s attempt=2 status=%s error=%s",
                query_id,
                stage,
                self._llm_error_status(exc),
                type(exc).__name__,
            )
            time.sleep(0.75)
            return invoke_fn()

    def _is_retryable_llm_error(self, exc: Exception) -> bool:
        """Determine whether an LLM exception should be retried.

        Args:
            exc: Exception raised by an LLM invocation.

        Returns:
            True when the exception status code is transient, otherwise False.
        """
        return self._llm_error_status(exc) in {429, 500, 502, 503, 504}

    def _llm_error_status(self, exc: Exception) -> int | None:
        """Extract an HTTP status code from an LLM exception when present.

        Args:
            exc: Exception raised by an LLM client.

        Returns:
            Integer HTTP status code if found, otherwise None.
        """
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int):
            return status_code

        response = getattr(exc, "response", None)
        response_status = getattr(response, "status_code", None)
        if isinstance(response_status, int):
            return response_status

        return None

    def _debug_log(self, message: str, *args: Any) -> None:
        """Emit concise RAG timing traces only when DEBUG=true.

        Args:
            message: Logging format string.
            *args: Values interpolated into the logging format string.

        Returns:
            None.
        """
        if getattr(getattr(self, "settings", None), "debug", False):
            logger.info("RAG_DEBUG " + message, *args)

    def _count_number_markers(self, text: str) -> int:
        """Count hidden number markers in markdown text."""
        return len(NUMBER_MARKER_PATTERN.findall(text or ""))

    def _normalize_mapped_fact_records(self, mapped_facts: MappedFacts) -> list[dict[str, Any]]:
        """Return JSON-ready mapped facts with responsiveness tiers."""
        records: list[dict[str, Any]] = []
        facts = mapped_facts.facts or []
        if not facts and mapped_facts.extracted_facts.strip():
            facts = [
                MappedFact(fact=line.strip(), responsiveness_tier="direct")
                for line in mapped_facts.extracted_facts.splitlines()
                if line.strip()
            ]

        for fact in facts:
            text = fact.fact.strip()
            if not text:
                continue
            tier = fact.responsiveness_tier
            records.append(
                {
                    "fact": text,
                    "responsiveness_tier": tier if tier in {"direct", "adjacent", "not_responsive"} else "direct",
                    "reason": fact.reason.strip(),
                    "source_numbers": [
                        candidate.model_dump(mode="json", exclude_none=True)
                        for candidate in fact.source_numbers
                    ],
                }
            )

        if not records:
            records.append(
                {
                    "fact": "- No relevant facts found.",
                    "responsiveness_tier": "not_responsive",
                    "reason": "No relevant evidence extracted from this chunk.",
                    "source_numbers": [],
                }
            )
        return records

    def _relevance_counts(self, facts: list[dict[str, Any]]) -> dict[str, int]:
        """Count mapped facts by responsiveness tier."""
        counts = {"direct": 0, "adjacent": 0, "not_responsive": 0}
        for fact in facts:
            tier = fact.get("responsiveness_tier")
            if tier in counts:
                counts[tier] += 1
        return counts

    def _merge_relevance_counts(self, counts_list: list[dict[str, int]]) -> dict[str, int]:
        """Merge responsiveness tier count dictionaries."""
        merged = {"direct": 0, "adjacent": 0, "not_responsive": 0}
        for counts in counts_list:
            for key in merged:
                merged[key] += int(counts.get(key, 0))
        return merged

    def _render_tiered_facts(self, facts: list[dict[str, Any]]) -> str:
        """Render mapped facts for reduce prompts while preserving tier metadata."""
        groups = [
            ("Direct facts", "direct"),
            ("Adjacent facts", "adjacent"),
            ("Not responsive facts", "not_responsive"),
        ]
        sections: list[str] = []
        for label, tier in groups:
            tier_facts = [fact for fact in facts if fact.get("responsiveness_tier") == tier]
            if not tier_facts:
                continue
            lines = [f"{label}:"]
            for fact in tier_facts:
                reason = fact.get("reason")
                suffix = f" (scope note: {reason})" if reason else ""
                lines.append(f"- {fact.get('fact', '').strip()}{suffix}")
            sections.append("\n".join(lines))
        return "\n\n".join(sections) or "Not responsive facts:\n- No relevant facts found."

    def _summarize_relevance(self, facts: list[dict[str, Any]], limit: int = 3) -> dict[str, Any]:
        """Build a compact relevance summary for logging and persistence."""
        direct = [fact.get("fact", "").strip() for fact in facts if fact.get("responsiveness_tier") == "direct"]
        adjacent = [
            {
                "fact": fact.get("fact", "").strip(),
                "reason": fact.get("reason", "").strip(),
            }
            for fact in facts
            if fact.get("responsiveness_tier") == "adjacent"
        ]
        return {
            "direct_examples": direct[:limit],
            "adjacent_examples": adjacent[:limit],
        }

    def _answer_budget_counts(self, text: str) -> dict[str, int]:
        """Return approximate word and bullet counts for generated answer budget logs."""
        return {
            "words": len(re.findall(r"\b\w+\b", text or "")),
            "bullets": len(re.findall(r"(?m)^\s*(?:[-*]|\d+\.)\s+", text or "")),
        }

    def _log_answer_budget(self, *, query_id: str, stage: str, label: str, text: str) -> None:
        """Log answers that exceed broad-answer budget targets."""
        counts = self._answer_budget_counts(text)
        if counts["words"] > 900 or counts["bullets"] > 14:
            self._debug_log(
                "answer_budget query_id=%s stage=%s label=%s words=%s bullets=%s target_words<=900 target_bullets<=14",
                query_id,
                stage,
                label,
                counts["words"],
                counts["bullets"],
            )

    def _unmarked_figures(self, text: str, limit: int = 12) -> list[str]:
        """Return displayed dollar figures that are not immediately followed by a marker."""
        figures: list[str] = []
        for match in FIGURE_PATTERN.finditer(text or ""):
            if self._immediate_number_marker(text, match.end()):
                continue
            figures.append(match.group(0))
            if len(figures) >= limit:
                break
        return figures

    def _immediate_number_marker(self, text: str, figure_end: int) -> re.Match[str] | None:
        """Return a marker only when it belongs to the figure that just ended."""
        suffix = (text or "")[figure_end : figure_end + 80]
        return re.match(r"^[\s,.;:)\*_~`]*\[\[num:([A-Za-z0-9_-]+)\]\]", suffix)

    def _emit_progress(self, state_or_query_id: RAGState | str, stage: str, message: str, **details: Any) -> None:
        """Emit query progress to an optional streaming callback.

        Args:
            state_or_query_id: Graph state or query id used to find the callback.
            stage: Machine-readable progress stage.
            message: Human-readable progress message.
            **details: Additional structured details included in the progress event.

        Returns:
            None.
        """
        query_id = state_or_query_id if isinstance(state_or_query_id, str) else state_or_query_id.get("query_id")
        if not query_id:
            return

        progress_lock = getattr(self, "_progress_lock", None)
        progress_callbacks = getattr(self, "_progress_callbacks", None)
        if progress_lock is None or progress_callbacks is None:
            return

        with progress_lock:
            callback = progress_callbacks.get(query_id)
        if not callback:
            return

        callback(
            {
                "query_id": query_id,
                "stage": stage,
                "message": message,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def _to_response(self, result: RAGState, processing_time: float, query_id: str) -> QueryResponse:
        """Convert final graph state into the public QueryResponse model.

        Args:
            result: Final graph state returned by LangGraph.
            processing_time: Total query processing time in seconds.
            query_id: Query identifier to expose in the API response.

        Returns:
            QueryResponse containing the final answer, divisions, sources, and metadata.
        """
        mapped_by_chunk = {chunk["chunk_id"]: chunk for chunk in result.get("mapped_chunks", []) if chunk["chunk_id"]}
        sources = self._source_documents(result, mapped_by_chunk) if result.get("include_sources") else None

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
            number_annotations=self._final_number_annotations(result),
            debug_division_queries=None,
            query_id=query_id,
            timestamp=datetime.utcnow(),
            thinking_speed=result.get("thinking_speed"),
            model_used=result.get("model_used"),
        )

    def _final_number_annotations(self, result: RAGState) -> list[NumberAnnotation]:
        """Return de-duplicated annotations whose markers appear in returned markdown."""
        annotations = self._annotations_from_dicts(result.get("number_annotations", []))
        by_id = {annotation.id: annotation for annotation in annotations}
        final: list[NumberAnnotation] = []

        for annotation_id, annotation in by_id.items():
            targets: list[NumberAnnotationTarget] = []
            if f"[[num:{annotation_id}]]" in result.get("final_answer", ""):
                targets.append(NumberAnnotationTarget(scope="answer"))

            for division in result.get("division_answers", []):
                if f"[[num:{annotation_id}]]" in division.get("answer", ""):
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
        self._debug_log(
            "response_annotations query_id=%s raw_annotations=%s unique_annotations=%s returned_annotations=%s "
            "returned_source=%s returned_derived=%s answer_markers=%s division_markers=%s "
            "unmarked_answer_figures=%s unmarked_division_figures=%s returned_ids=%s returned_figures=%s",
            result.get("query_id", "unknown"),
            len(annotations),
            len(by_id),
            len(final),
            sum(1 for annotation in final if annotation.kind == "source"),
            sum(1 for annotation in final if annotation.kind == "derived"),
            self._count_number_markers(answer),
            self._count_number_markers(division_answers),
            self._unmarked_figures(answer),
            self._unmarked_figures(division_answers),
            [annotation.id for annotation in final[:20]],
            [annotation.figure for annotation in final[:20]],
        )
        return final

    def _source_documents(
        self,
        result: RAGState,
        mapped_by_chunk: dict[str, MappedChunkState],
    ) -> list[SourceDocument]:
        """Build source document records from retrieved and mapped chunks.

        Args:
            result: Final graph state containing retrieved chunks.
            mapped_by_chunk: Mapped chunks keyed by stable chunk id.

        Returns:
            SourceDocument records for API and saved-result display.
        """
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

    def _source_number_annotations(
        self,
        chunk: RetrievedChunkState,
        extracted_facts: str,
        candidates: list[SourceNumberCandidate],
    ) -> list[NumberAnnotation]:
        """Build source-backed annotations from relevant mapped facts."""
        if not chunk["chunk_id"]:
            return []

        annotations: list[NumberAnnotation] = []
        seen_keys: set[tuple[str, str]] = set()
        source_candidates = candidates or self._fallback_source_number_candidates(extracted_facts)
        for index, candidate in enumerate(source_candidates, start=1):
            figure = candidate.figure.strip()
            value = candidate.value if candidate.value is not None else self._normalize_figure(figure)
            if value is None:
                continue
            if figure not in extracted_facts or figure not in chunk["content"]:
                continue

            label = candidate.label.strip() or self._source_label(extracted_facts, figure)
            seen_key = (figure.lower(), label.lower())
            if seen_key in seen_keys:
                continue
            seen_keys.add(seen_key)

            marker_id = self._annotation_id("src", chunk["division_acronym"], chunk["chunk_id"], str(index))
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

    def _mark_text_with_source_annotations(self, text: str, annotations: list[NumberAnnotation]) -> str:
        """Add hidden source markers to extracted fact text when figures match chunk evidence."""
        by_figure: dict[str, list[NumberAnnotation]] = {}
        for annotation in annotations:
            by_figure.setdefault(annotation.figure.lower(), []).append(annotation)

        used_by_figure: dict[str, int] = {}

        def replace(match: re.Match[str]) -> str:
            figure = match.group(0)
            if self._immediate_number_marker(text, match.end()):
                return figure
            candidates = by_figure.get(figure.lower(), [])
            if candidates:
                key = figure.lower()
                candidate_index = min(used_by_figure.get(key, 0), len(candidates) - 1)
                used_by_figure[key] = used_by_figure.get(key, 0) + 1
                return f"{figure} [[num:{candidates[candidate_index].id}]]"
            return figure

        return FIGURE_PATTERN.sub(replace, text)

    def _fallback_source_number_candidates(self, extracted_facts: str) -> list[SourceNumberCandidate]:
        """Build source candidates from mapped facts when structured map output is unavailable."""
        candidates: list[SourceNumberCandidate] = []
        for match in FIGURE_PATTERN.finditer(extracted_facts):
            figure = match.group(0)
            value = self._normalize_figure(figure)
            if value is None:
                continue
            candidates.append(
                SourceNumberCandidate(
                    figure=figure,
                    value=value,
                    label=self._source_label(extracted_facts, figure),
                )
            )
        return candidates

    def _invoke_mapped_facts(self, llm: Any, prompt: str, *, stage: str, query_id: str) -> MappedFacts:
        """Invoke structured map output, falling back to plain extracted facts."""
        try:
            structured_llm = llm.with_structured_output(MappedFacts)
        except AttributeError:
            text = self._invoke_text(llm, prompt, stage=stage, query_id=query_id)
            return MappedFacts(extracted_facts=text, source_numbers=self._fallback_source_number_candidates(text))

        try:
            response = self._invoke_with_retry(
                lambda: structured_llm.invoke(prompt),
                stage=stage,
                query_id=query_id,
            )
        except Exception:
            text = self._invoke_text(llm, prompt, stage=stage, query_id=query_id)
            return MappedFacts(extracted_facts=text, source_numbers=self._fallback_source_number_candidates(text))

        if isinstance(response, MappedFacts):
            return response
        if isinstance(response, dict):
            return MappedFacts.model_validate(response)
        return MappedFacts.model_validate(getattr(response, "model_dump", lambda: response)())

    def _invoke_marked_answer(self, llm: Any, prompt: str, *, stage: str, query_id: str) -> MarkedAnswer:
        """Invoke structured answer output, falling back to plain markdown for legacy models/tests."""
        try:
            structured_llm = llm.with_structured_output(MarkedAnswer)
        except AttributeError:
            return MarkedAnswer(answer=self._invoke_text(llm, prompt, stage=stage, query_id=query_id))

        try:
            response = self._invoke_with_retry(
                lambda: structured_llm.invoke(prompt),
                stage=stage,
                query_id=query_id,
            )
        except Exception:
            return MarkedAnswer(answer=self._invoke_text(llm, prompt, stage=stage, query_id=query_id))

        if isinstance(response, MarkedAnswer):
            return response
        if isinstance(response, dict):
            return MarkedAnswer.model_validate(response)
        return MarkedAnswer.model_validate(getattr(response, "model_dump", lambda: response)())

    def _validate_derived_annotations(
        self,
        *,
        proposed: list[ProposedDerivedAnnotation],
        target_answer: str,
        available: list[NumberAnnotation],
        target: NumberAnnotationTarget,
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

            displayed_figure = self._displayed_figure_for_marker(target_answer, proposal.id)
            displayed_value = self._normalize_figure(displayed_figure) if displayed_figure else None
            if displayed_value is None:
                reject("missing_or_unparseable_displayed_marker_figure", proposal)
                continue

            source_input_ids = self._flatten_source_input_ids(proposal.input_ids, available_by_id)
            if not source_input_ids:
                reject("no_source_backed_inputs", proposal)
                continue

            input_total = sum(available_by_id[source_id].value for source_id in source_input_ids)
            proposed_value = proposal.value
            if not self._values_close(displayed_value, proposed_value):
                reject("displayed_proposed_value_mismatch", proposal)
                continue
            if not self._values_close(displayed_value, input_total):
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
            self._debug_log(
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

    def _displayed_figure_for_marker(self, text: str, marker_id: str) -> str | None:
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

    def _flatten_source_input_ids(
        self,
        input_ids: list[str],
        available_by_id: dict[str, NumberAnnotation],
    ) -> list[str]:
        """Flatten source and nested derived inputs into source annotation ids."""
        source_ids: list[str] = []
        seen_source_ids: set[str] = set()

        def visit(annotation_id: str, stack: set[str]) -> bool:
            if annotation_id in stack:
                return False
            annotation = available_by_id.get(annotation_id)
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
            return all(visit(child_id, stack | {annotation_id}) for child_id in child_ids)

        return source_ids if all(visit(input_id, set()) for input_id in input_ids) else []

    def _annotations_from_dicts(self, annotations: Any) -> list[NumberAnnotation]:
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

    def _annotation_prompt_context(self, annotations: list[NumberAnnotation]) -> str:
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

    def _normalize_figure(self, figure: str) -> float | None:
        """Normalize a displayed dollar figure to dollars."""
        return self.parse_dollar_figure(figure)

    def parse_dollar_figure(self, text: str) -> float | None:
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
        multiplier = {
            "thousand": 1_000,
            "million": 1_000_000,
            "billion": 1_000_000_000,
            "trillion": 1_000_000_000_000,
        }.get((scale or "").lower(), 1)
        return value * multiplier

    def _values_close(self, left: float, right: float) -> bool:
        """Compare normalized dollar values with a small display-rounding tolerance."""
        tolerance = max(1.0, abs(left) * 0.01)
        return abs(left - right) <= tolerance

    def _annotation_id(self, *parts: str) -> str:
        """Build a marker-safe deterministic annotation id."""
        raw = "_".join(parts).lower()
        safe = re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")
        if len(safe) <= 80:
            return safe
        suffix = uuid.uuid5(uuid.NAMESPACE_URL, raw).hex[:10]
        return f"{safe[:68].rstrip('_')}_{suffix}"

    def _source_label(self, extracted_facts: str, figure: str) -> str:
        """Build a short label for source-backed figure popovers from mapped facts."""
        for line in extracted_facts.splitlines():
            if figure in line:
                label = re.sub(r"\s+", " ", line).strip(" -*")
                return label[:117].rstrip() + "..." if len(label) > 120 else label
        label = re.sub(r"\s+", " ", extracted_facts).strip(" -*")
        if not label:
            return "Source-backed figure"
        return label[:117].rstrip() + "..." if len(label) > 120 else label

    def _debug_division_queries(self, result: RAGState) -> list[DebugDivisionQuery]:
        """Build debug records showing the retrieval query used for each division.

        Args:
            result: Final graph state containing division query decisions.

        Returns:
            DebugDivisionQuery records for optional debug output.
        """
        return [
            DebugDivisionQuery(
                division=item["division"],
                division_acronym=item["division_acronym"],
                query=item["query"],
            )
            for item in result.get("division_queries", [])
        ]

    async def ingest_data(
        self,
        embedding_model: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        clear_existing: bool = True,
        ingest_id: Optional[str] = None,
        name: str | None = None,
        activate: bool = True,
    ) -> tuple[IngestResponse, str]:
        """Create a versioned vector store by ingesting all configured bill divisions.

        Args:
            embedding_model: Embedding model used to vectorize source chunks.
            chunk_size: Optional character count per chunk.
            chunk_overlap: Optional character overlap between adjacent chunks.
            clear_existing: Whether to clear the target vector-store directory first.
            ingest_id: Optional external ingestion identifier for logging.
            name: Optional display name for the vector store registry row.
            activate: Whether to make the new vector store active after success.

        Returns:
            Tuple of ingestion API response and embedding model used.
        """
        start_time = time.time()
        ingest_id = ingest_id or f"ingest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        logger.info("Starting ingestion %s with embedding model %s", ingest_id, embedding_model)
        chunk_size = chunk_size or self.settings.chunk_size
        chunk_overlap = chunk_overlap if chunk_overlap is not None else self.settings.chunk_overlap

        if not database_available() or SessionLocal is None:
            raise ValueError("Storage metadata is unavailable")

        with SessionLocal() as db:
            store = create_vector_store_record(
                db,
                name=name or f"{embedding_model} ({chunk_size})",
                embedding_model=embedding_model,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                activate=activate,
            )
            db.commit()
            db.refresh(store)

        try:
            self.vectorstores.clear_cached_stores()
            target_dir = vector_store_path(store)
            divisions_processed, partitions, total_chunks = self.ingestion.ingest(
                embedding_model=embedding_model,
                clear_existing=clear_existing,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                vectorstore_dir=target_dir,
                vector_store_id=store.id,
            )
            self.vectorstores.reset_embedding_model(embedding_model)
            self.settings.embedding_model = embedding_model
            self.settings.chunk_size = chunk_size
            self.settings.chunk_overlap = chunk_overlap
            with SessionLocal() as db:
                store = db.get(type(store), store.id)
                if store:
                    mark_vector_store_ready(db, store, partitions, total_chunks, activate=activate)
                    db.commit()
        except Exception as exc:
            elapsed = time.time() - start_time
            try:
                with SessionLocal() as db:
                    failed_store = db.get(type(store), store.id)
                    if failed_store:
                        mark_vector_store_failed(db, failed_store, str(exc))
                        db.commit()
            except Exception:
                pass
            logger.error("Ingestion %s failed after %.2fs: %s", ingest_id, elapsed, exc, exc_info=True)
            raise Exception(f"Ingestion failed after {elapsed:.1f} seconds: {exc}") from exc

        processing_time = time.time() - start_time
        return (
            IngestResponse(
                status="completed",
                message=f"Successfully ingested {divisions_processed} divisions using {embedding_model}",
                embedding_model=embedding_model,
                divisions_processed=divisions_processed,
                chunk_size=chunk_size or self.settings.chunk_size,
                processing_time=processing_time,
            ),
            embedding_model,
        )

    async def health_check(self) -> dict[str, str]:
        """Report whether retrieval and optional history storage are available.

        Args:
            None.

        Returns:
            Dictionary with health status, database status, history availability, and model metadata.
        """
        try:
            if database_available() and SessionLocal is not None:
                try:
                    with SessionLocal() as db:
                        active_store = get_active_vector_store(db)
                    if active_store:
                        return {
                            "status": "healthy",
                            "database_status": "connected",
                            "history_available": "true",
                            "available_divisions": str(len(self.settings.subcommittee_stores)),
                            "embedding_model": active_store.embedding_model_id,
                            "active_vector_store": active_store.name,
                        }
                except Exception as exc:
                    logger.warning("Storage registry unavailable during health check: %s", exc)

            vectorstore_dir = str(self.settings.vectorstore_dir)
            available_stores = [
                name
                for name in os.listdir(vectorstore_dir)
                if os.path.isdir(os.path.join(vectorstore_dir, name)) and name != "vector_stores"
            ]
            if not available_stores:
                return {"status": "unhealthy", "reason": "No vector databases found"}
            return {
                "status": "healthy",
                "database_status": "connected",
                "history_available": "false",
                "available_divisions": str(len(self.settings.subcommittee_stores)),
                "embedding_model": self.vectorstores.embedding_model,
            }
        except Exception as exc:
            return {"status": "unhealthy", "reason": f"Database connectivity issue: {exc}"}


_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the process-wide RAG service instance.

    Args:
        None.

    Returns:
        Singleton RAGService used by API endpoints.
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
