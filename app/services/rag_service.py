"""LangGraph RAG orchestration for LawSearch AI."""

from __future__ import annotations

import logging
import operator
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Lock
from typing import Annotated, Any, Callable, Optional

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
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.core.config import get_settings
from app.db.models import VectorStore
from app.db.session import SessionLocal, database_available
from app.models.query import (
    DebugChunk,
    DebugDivisionQuery,
    DivisionResult,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceDocument,
)
from app.services.ingestion_service import IngestionService
from app.services.llm_factory import create_chat_model, describe_model_strategy, format_model_spec, resolve_model
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


class RouteDecision(BaseModel):
    """Structured routing response."""

    divisions: list[str] = Field(default_factory=list)


class DivisionQueryDecision(BaseModel):
    """Structured per-division retrieval query response."""

    division: str
    query: str


class DivisionQueryPlan(BaseModel):
    """Structured query rewrite response."""

    division_queries: list[DivisionQueryDecision] = Field(default_factory=list)


class DivisionQueryState(TypedDict):
    division: str
    division_acronym: str
    query: str


class RetrievedChunkState(TypedDict):
    chunk_id: str
    division: str
    division_acronym: str
    content: str
    chunk_summary: str | None
    score: float | None
    metadata: dict[str, Any]


class MappedChunkState(TypedDict):
    chunk_id: str
    division: str
    division_acronym: str
    extracted_facts: str
    chunk_summary: str
    chunk_snapshot: str
    source_content: str
    score: float | None
    metadata: dict[str, Any]


class DivisionAnswerState(TypedDict):
    division: str
    division_acronym: str
    answer: str
    source_chunk_ids: list[str]
    chunks_retrieved: int


class RAGState(TypedDict, total=False):
    query_id: str
    question: str
    thinking_speed: str
    max_results: int
    include_sources: bool
    debug_chunks: bool
    divisions_filter: list[str] | None
    model_used: str
    vector_store_id: str | None
    vector_store_root: str | None
    vector_store_embedding_model: str | None
    selected_divisions: list[str]
    division_queries: list[DivisionQueryState]
    retrieved_chunks: Annotated[list[RetrievedChunkState], operator.add]
    mapped_chunks: Annotated[list[MappedChunkState], operator.add]
    division_answers: Annotated[list[DivisionAnswerState], operator.add]
    final_answer: str


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
            "debug_chunks": bool(request.debug_chunks),
            "divisions_filter": request.divisions_filter,
            "model_used": model_used,
            "vector_store_id": active_store_id,
            "vector_store_root": active_store_root,
            "vector_store_embedding_model": active_embedding_model,
            "selected_divisions": [],
            "division_queries": [],
            "retrieved_chunks": [],
            "mapped_chunks": [],
            "division_answers": [],
            "final_answer": "",
        }
        self._debug_log(
            "query_start query_id=%s speed=%s model=%s max_results=%s include_sources=%s "
            "debug_chunks=%s filter_count=%s question_chars=%s",
            query_id,
            thinking_speed,
            model_used,
            state["max_results"],
            state["include_sources"],
            state["debug_chunks"],
            len(request.divisions_filter or []),
            len(request.question),
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
            "mapped_chunks=%s division_answers=%s",
            query_id,
            processing_time,
            len(result.get("selected_divisions", [])),
            len(result.get("retrieved_chunks", [])),
            len(result.get("mapped_chunks", [])),
            len(result.get("division_answers", [])),
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
                    save_query_response(db, response=response, question=request.question, vector_store=vector_store)
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
        if requested_filter:
            self._debug_log(
                "route query_id=%s source=filter duration=%.2fs selected=%s",
                state.get("query_id", "unknown"),
                time.time() - start_time,
                len(requested_filter),
            )
            return {"selected_divisions": requested_filter}

        valid_divisions = list(self.settings.subcommittee_stores.keys())
        routing_model = resolve_model(state.get("thinking_speed", "normal"), "routing")
        routing_llm = create_chat_model(
            routing_model.model,
            "routing",
            routing_model.reasoning_effort,
        ).with_structured_output(RouteDecision)
        allowed_divisions = "\n- ".join(valid_divisions)
        route_messages = [
            SystemMessage(
                content=(
                    "Select the relevant appropriations divisions for this question. "
                    "Return only exact division names from the allowed list."
                )
            ),
            HumanMessage(
                content=(
                    f"Allowed divisions:\n- {allowed_divisions}\n\n"
                    f"Question: {state['question']}"
                )
            ),
        ]
        decision = self._invoke_with_retry(
            lambda: routing_llm.invoke(route_messages),
            stage="route",
            query_id=state.get("query_id", "unknown"),
        )
        selected = [division for division in decision.divisions if division in self.settings.subcommittee_stores]
        if not selected:
            logger.warning("Router returned no valid divisions; querying all divisions as fallback")
            selected = valid_divisions
        self._debug_log(
            "route query_id=%s source=llm model=%s duration=%.2fs selected=%s divisions=%s",
            state.get("query_id", "unknown"),
            format_model_spec(routing_model),
            time.time() - start_time,
            len(selected),
            [division_acronym(division) for division in selected],
        )
        return {"selected_divisions": selected}

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
        try:
            chunks = self.vectorstores.retrieve(
                question=retrieval_query,
                division=division,
                k=state["max_results"],
                vectorstore_root=state.get("vector_store_root"),
                embedding_model=state.get("vector_store_embedding_model"),
            )
        except TypeError:
            chunks = self.vectorstores.retrieve(retrieval_query, division, state["max_results"])
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

        extraction_prompt = (
            "You are a legislative financial analyst extracting evidence from one source chunk.\n\n"
            "Return only markdown bullets using this format:\n"
            "- <specific fact with exact dollar figure/account/program/agency/fiscal year if present> "
            f"[{chunk['division_acronym']}]\n\n"
            "Rules:\n"
            "- Extract only facts that help answer the question.\n"
            "- Preserve exact dollar figures, account names, agencies, fiscal years, and section references.\n"
            "- One fact per bullet; no paragraphs.\n"
            "- End every substantive bullet with the citation marker.\n"
            "- If the chunk has no relevant evidence, return exactly: - No relevant facts found.\n\n"
            f"Question:\n{question}\n\n"
            f"Source chunk:\n{chunk['content']}"
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
                self._invoke_text,
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
            extracted_facts = facts_future.result()
            chunk_summary = summary_future.result()
            chunk_snapshot = snapshot_future.result()

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
        }
        self._debug_log(
            "map query_id=%s chunk_id=%s division=%s map_model=%s summary_model=%s duration=%.2fs facts_chars=%s summary_chars=%s snapshot_chars=%s",
            state.get("query_id", "unknown"),
            chunk["chunk_id"],
            chunk["division_acronym"],
            format_model_spec(map_model),
            format_model_spec(summary_model),
            time.time() - start_time,
            len(extracted_facts),
            len(chunk_summary),
            len(chunk_snapshot),
        )
        return {"mapped_chunks": [mapped]}

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
        if not facts.strip():
            answer = "No relevant facts found for this division."
        else:
            prompt = (
                "Synthesize the extracted facts into a division-level answer with a fixed structure.\n\n"
                "Use this exact markdown structure:\n"
                f"### [{state['division_acronym']}] {division}\n"
                "- **Bottom line:** <1-2 sentence direct answer for this division.>\n"
                "- **Accounts / programs:**\n"
                "  - <account/program/agency and exact dollar figure, preserving citation marker>\n"
                "- **Notes:**\n"
                "  - <short caveat, limitation, transfer detail, or availability note; use 'None identified.' if none>\n\n"
                "Rules:\n"
                "- Preserve all relevant dollar figures from the extracted facts.\n"
                "- Keep citation markers immediately after the figure or clause they support.\n"
                "- Do not invent totals unless the extracted facts explicitly support the arithmetic.\n"
                "- Do not omit relevant accounts or programs just to be concise.\n"
                "- If the facts do not answer the question, say so in the bottom line.\n\n"
                f"Question:\n{state['question']}\n\n"
                f"Division: {division}\n\n"
                f"Extracted facts:\n{facts}"
            )
            answer = self._invoke_text(
                llm,
                prompt,
                stage="reduce",
                query_id=state.get("query_id", "unknown"),
            )

        division_answer: DivisionAnswerState = {
            "division": division,
            "division_acronym": state["division_acronym"],  # type: ignore[typeddict-item]
            "answer": answer,
            "source_chunk_ids": [item["chunk_id"] for item in mapped_items],
            "chunks_retrieved": chunks_retrieved,
        }
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
        return {"division_answers": [division_answer]}

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
            f"## {item['division']} [{item['division_acronym']}]\n{item['answer']}"
            for item in division_answers
        )
        prompt = (
            "Create the final answer from the division-level answers using a stable structure.\n\n"
            "Use this exact markdown structure:\n"
            "## Answer\n"
            "- <short direct answer to the user's question.>\n\n"
            "## By Division\n"
            "### [ACRONYM] Division Name\n"
            "- **Bottom line:** <division bottom line>\n"
            "- **Accounts / programs:**\n"
            "  - <account/program and exact dollar figure with citation marker>\n"
            "- **Notes:**\n"
            "  - <caveat/limitation/transfer/availability note or 'None identified.'>\n\n"
            "## Caveats\n"
            "- <only include important caveats about totals, transfers, offsets, or incomplete comparability.>\n\n"
            "Rules:\n"
            "- Include every division answer provided below; do not drop a division.\n"
            "- Preserve relevant dollar figures and citation markers from division answers.\n"
            "- Keep citation markers immediately after the figure or clause they support.\n"
            "- Combine figures only when they are clearly comparable and supported by the division answers.\n"
            "- If no caveats are needed, write '- None identified.'\n"
            "- Use clear language, clear numbers, and no filler.\n\n"
            f"Question:\n{state['question']}\n\n"
            f"Division answers:\n{context}"
        )
        final_answer = self._invoke_text(
            llm,
            prompt,
            stage="synthesize",
            query_id=state.get("query_id", "unknown"),
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
        return {"final_answer": final_answer}

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
        mapped_by_chunk = {chunk["chunk_id"]: chunk for chunk in result.get("mapped_chunks", [])}
        sources = self._source_documents(result, mapped_by_chunk) if result.get("include_sources") else None
        debug_chunks = self._debug_chunks(result, mapped_by_chunk) if result.get("debug_chunks") else None
        debug_division_queries = self._debug_division_queries(result) if result.get("debug_chunks") else None

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
            debug_chunks=debug_chunks,
            debug_division_queries=debug_division_queries,
            query_id=query_id,
            timestamp=datetime.utcnow(),
            thinking_speed=result.get("thinking_speed"),
            model_used=result.get("model_used"),
        )

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
                chunk_id=chunk["chunk_id"],
                content_snippet=chunk["content"],
                chunk_summary=mapped_by_chunk.get(chunk["chunk_id"], {}).get("chunk_summary"),
                chunk_snapshot=mapped_by_chunk.get(chunk["chunk_id"], {}).get("chunk_snapshot"),
                confidence_score=None,
                metadata=chunk.get("metadata", {}),
            )
            for chunk in result.get("retrieved_chunks", [])
        ]

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

    def _debug_chunks(
        self,
        result: RAGState,
        mapped_by_chunk: dict[str, MappedChunkState],
    ) -> list[DebugChunk]:
        """Build debug chunk payloads with full source content and map summaries.

        Args:
            result: Final graph state containing retrieved chunks.
            mapped_by_chunk: Mapped chunks keyed by stable chunk id.

        Returns:
            DebugChunk records for optional debug output.
        """
        return [
            DebugChunk(
                chunk_id=chunk["chunk_id"],
                division=chunk["division"],
                division_acronym=chunk["division_acronym"],
                content=chunk["content"],
                chunk_summary=mapped_by_chunk.get(chunk["chunk_id"], {}).get("chunk_summary"),
                chunk_snapshot=mapped_by_chunk.get(chunk["chunk_id"], {}).get("chunk_snapshot"),
                score=chunk.get("score"),
                metadata=chunk.get("metadata", {}),
            )
            for chunk in result.get("retrieved_chunks", [])
        ]

    async def ingest_data(
        self,
        embedding_model: str,
        chunk_size: int | None = None,
        clear_existing: bool = True,
        ingest_id: Optional[str] = None,
        name: str | None = None,
        activate: bool = True,
    ) -> tuple[IngestResponse, str]:
        """Create a versioned vector store by ingesting all configured bill divisions.

        Args:
            embedding_model: Embedding model used to vectorize source chunks.
            chunk_size: Optional character count per chunk.
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

        if not database_available() or SessionLocal is None:
            raise ValueError("Storage metadata is unavailable")

        with SessionLocal() as db:
            store = create_vector_store_record(
                db,
                name=name or f"{embedding_model} ({chunk_size})",
                embedding_model=embedding_model,
                chunk_size=chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
                activate=activate,
            )
            db.commit()
            db.refresh(store)

        try:
            self.vectorstores.clear_cached_stores()
            target_dir = vector_store_path(store)
            divisions_processed, partitions, total_chunks = self.ingestion.ingest(
                embedding_model,
                clear_existing,
                chunk_size,
                vectorstore_dir=target_dir,
                vector_store_id=store.id,
            )
            self.vectorstores.reset_embedding_model(embedding_model)
            self.settings.embedding_model = embedding_model
            self.settings.chunk_size = chunk_size
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
