"""LangGraph RAG orchestration for LawSearch AI.

This module is a thin host. The Query Pipeline stages, the Number Annotation
pipeline, structured-LLM helpers, response shaping, and other subsystems live
in sibling modules under :mod:`app.services.rag`. ``RAGService`` owns runtime
dependencies (settings, vector store, ingestion service, progress callback
registry) and binds the LangGraph nodes to the pure stage functions.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Optional

# In local development, Chroma may need the pysqlite3 shim. Docker uses system sqlite.
if os.getenv("ENVIRONMENT") != "production" and not os.path.exists("/.dockerenv"):
    try:
        import pysqlite3  # type: ignore[import-not-found]

        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        pass

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.core.config import get_settings
from app.db.models import VectorStore
from app.db.session import SessionLocal, database_available
from app.models.query import (
    IngestResponse,
    NumberAnnotation,
    NumberAnnotationTarget,
    QueryRequest,
    QueryResponse,
)
from app.services.ingestion_service import IngestionService
from app.services.embedding_factory import ensure_embedding_model_available
from app.services.llm_factory import describe_model_strategy
from app.services.rag.annotations import (
    mark_text_with_source_annotations,
    parse_dollar_figure,
    source_number_annotations,
    unmarked_figures,
    validate_derived_annotations,
)
from app.services.rag.context import RAGContext
from app.services.rag.llm_invocation import invoke_text
from app.services.rag.response import to_response
from app.services.rag.schemas import ProposedDerivedAnnotation, SourceNumberCandidate
from app.services.rag.stages.classify import classify_answer_mode
from app.services.rag.stages.map_chunk import fan_out_chunks, map_chunk, send_chunks_to_map
from app.services.rag.stages.reduce import (
    fan_out_reduce_divisions,
    reduce_division,
    send_divisions_to_reduce,
)
from app.services.rag.stages.retrieve import fan_out_divisions, retrieve_division
from app.services.rag.stages.rewrite import rewrite_division_queries
from app.services.rag.stages.route import route_divisions
from app.services.rag.stages.synthesize import synthesize_final
from app.services.rag.state import RAGState, RetrievedChunkState, retrieval_k_for_request
from app.services.rag_prompting import DEFAULT_ANSWER_MODE
from app.services.storage_registry import (
    create_vector_store_record,
    ensure_storage_ready,
    get_active_vector_store,
    mark_vector_store_failed,
    mark_vector_store_ready,
    save_query_response,
    vector_store_path,
)
from app.services.vector_store_service import VectorStoreService


logger = logging.getLogger(__name__)


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

    def _make_ctx(self) -> RAGContext:
        """Build a fresh RAGContext bound to current dependencies.

        Built on demand instead of cached so tests that construct partial
        ``RAGService`` instances (e.g. via ``RAGService.__new__``) can set
        ``settings`` and ``vectorstores`` directly without juggling a cached
        context.
        """
        return RAGContext(
            settings=getattr(self, "settings", None),
            vectorstores=getattr(self, "vectorstores", None),
            emit_progress=self._emit_progress,
            debug_log=self._debug_log,
        )

    def _build_graph(self):
        """Build and compile the LangGraph workflow used for every query.

        Args:
            None.

        Returns:
            A compiled LangGraph application that transforms RAGState into final query state.
        """
        builder = StateGraph(RAGState)
        builder.add_node("classify_answer_mode", self._classify_answer_mode)
        builder.add_node("route_divisions", self._route_divisions)
        builder.add_node("rewrite_division_queries", self._rewrite_division_queries)
        builder.add_node("retrieve_division", self._retrieve_division)
        builder.add_node("fan_out_chunks", self._fan_out_chunks)
        builder.add_node("map_chunk", self._map_chunk)
        builder.add_node("fan_out_reduce_divisions", self._fan_out_reduce_divisions)
        builder.add_node("reduce_division", self._reduce_division)
        builder.add_node("synthesize_final", self._synthesize_final)

        builder.add_edge(START, "classify_answer_mode")
        builder.add_edge("classify_answer_mode", "route_divisions")
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
            "include_sources": bool(request.include_sources),
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

    def _classify_answer_mode(self, state: RAGState) -> dict[str, Any]:
        """Classify the requested answer shape before division routing."""
        return classify_answer_mode(state, self._make_ctx())

    def _route_divisions(self, state: RAGState) -> dict[str, Any]:
        """Select which appropriations divisions should be searched for the query."""
        return route_divisions(state, self._make_ctx())

    def _rewrite_division_queries(self, state: RAGState) -> dict[str, Any]:
        """Rewrite the original question into division-specific retrieval queries."""
        return rewrite_division_queries(state, self._make_ctx())

    def _fan_out_divisions(self, state: RAGState) -> list[Send]:
        """Create LangGraph Send events that retrieve chunks for each selected division."""
        return fan_out_divisions(state, self._make_ctx())

    def _retrieve_division(self, state: RAGState) -> dict[str, Any]:
        """Retrieve relevant source chunks for one division from the active vector store."""
        return retrieve_division(state, self._make_ctx())

    def _fan_out_chunks(self, state: RAGState) -> dict[str, Any]:
        """Provide a graph synchronization point before chunk mapping."""
        return fan_out_chunks(state, self._make_ctx())

    def _send_chunks_to_map(self, state: RAGState) -> list[Send]:
        """Create LangGraph Send events that map every retrieved chunk independently."""
        return send_chunks_to_map(state, self._make_ctx())

    def _map_chunk(self, state: RAGState) -> dict[str, Any]:
        """Extract relevant facts and UI summaries from one retrieved chunk."""
        return map_chunk(state, self._make_ctx())

    def _fan_out_reduce_divisions(self, state: RAGState) -> dict[str, Any]:
        """Provide a graph synchronization point before division reduction."""
        return fan_out_reduce_divisions(state, self._make_ctx())

    def _send_divisions_to_reduce(self, state: RAGState) -> list[Send]:
        """Group mapped chunks by division and create reduction Send events."""
        return send_divisions_to_reduce(state, self._make_ctx())

    def _reduce_division(self, state: RAGState) -> dict[str, Any]:
        """Synthesize mapped chunk facts into one division-level answer."""
        return reduce_division(state, self._make_ctx())

    def _synthesize_final(self, state: RAGState) -> dict[str, Any]:
        """Combine division-level answers into the final response text."""
        return synthesize_final(state, self._make_ctx())

    def _invoke_text(self, llm: Any, prompt: str, *, stage: str, query_id: str) -> str:
        """Invoke an LLM and normalize its response content to plain text."""
        return invoke_text(
            llm,
            prompt,
            stage=stage,
            query_id=query_id,
            debug_log=self._debug_log,
        )

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

    def _unmarked_figures(self, text: str, limit: int = 12) -> list[str]:
        """Return displayed dollar figures that are not immediately followed by a marker."""
        return unmarked_figures(text, limit=limit)

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
        """Convert final graph state into the public QueryResponse model."""
        return to_response(
            result,
            processing_time,
            query_id,
            debug_log=self._debug_log,
            debug_enabled=bool(getattr(getattr(self, "settings", None), "debug", False)),
        )

    def _source_number_annotations(
        self,
        chunk: RetrievedChunkState,
        extracted_facts: str,
        candidates: list[SourceNumberCandidate],
    ) -> list[NumberAnnotation]:
        """Build source-backed annotations from relevant mapped facts."""
        return source_number_annotations(chunk, extracted_facts, candidates)

    def _mark_text_with_source_annotations(self, text: str, annotations: list[NumberAnnotation]) -> str:
        """Add hidden source markers to extracted fact text when figures match chunk evidence."""
        return mark_text_with_source_annotations(text, annotations)

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
        return validate_derived_annotations(
            proposed=proposed,
            target_answer=target_answer,
            available=available,
            target=target,
            debug_log=self._debug_log,
            query_id=query_id,
            stage=stage,
            target_label=target_label,
        )

    def parse_dollar_figure(self, text: str) -> float | None:
        """Parse a displayed dollar figure into normalized dollars."""
        return parse_dollar_figure(text)

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

        ensure_embedding_model_available(embedding_model, self.settings)

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
