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
from typing import Annotated, Any, Optional

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
from app.models.query import (
    DebugChunk,
    DivisionResult,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceDocument,
)
from app.services.ingestion_service import IngestionService
from app.services.llm_factory import create_chat_model, resolve_model
from app.services.vector_store_service import VectorStoreService, division_acronym

logger = logging.getLogger(__name__)


class RouteDecision(BaseModel):
    """Structured routing response."""

    divisions: list[str] = Field(default_factory=list)


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
    question: str
    thinking_speed: str
    max_results: int
    include_sources: bool
    debug_chunks: bool
    divisions_filter: list[str] | None
    model_override: str | None
    model_used: str
    selected_divisions: list[str]
    retrieved_chunks: Annotated[list[RetrievedChunkState], operator.add]
    mapped_chunks: Annotated[list[MappedChunkState], operator.add]
    division_answers: Annotated[list[DivisionAnswerState], operator.add]
    final_answer: str


def retrieval_k_for_request(request: QueryRequest) -> int:
    """Request max_results means chunks per division."""
    return request.max_results or get_settings().default_results_per_division


class RAGService:
    """Coordinates routing, retrieval, mapping, reduction, and ingestion."""

    def __init__(self):
        self.settings = get_settings()
        self.vectorstores = VectorStoreService()
        self.settings.embedding_model = self.vectorstores.embedding_model
        self.ingestion = IngestionService()
        self._graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(RAGState)
        builder.add_node("route_divisions", self._route_divisions)
        builder.add_node("retrieve_division", self._retrieve_division)
        builder.add_node("fan_out_chunks", self._fan_out_chunks)
        builder.add_node("map_chunk", self._map_chunk)
        builder.add_node("fan_out_reduce_divisions", self._fan_out_reduce_divisions)
        builder.add_node("reduce_division", self._reduce_division)
        builder.add_node("synthesize_final", self._synthesize_final)

        builder.add_edge(START, "route_divisions")
        builder.add_conditional_edges(
            "route_divisions",
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
    ) -> QueryResponse:
        start_time = time.time()
        query_id = query_id or f"query_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        thinking_speed = request.thinking_speed or "normal"
        model_used = resolve_model(thinking_speed, request.model_override)

        state: RAGState = {
            "question": request.question,
            "thinking_speed": thinking_speed,
            "max_results": retrieval_k_for_request(request),
            "include_sources": bool(request.include_sources),
            "debug_chunks": bool(request.debug_chunks),
            "divisions_filter": request.divisions_filter,
            "model_override": request.model_override,
            "model_used": model_used,
            "selected_divisions": [],
            "retrieved_chunks": [],
            "mapped_chunks": [],
            "division_answers": [],
            "final_answer": "",
        }

        try:
            result = self._graph.invoke(state, config={"recursion_limit": 50})
        except Exception as exc:
            processing_time = time.time() - start_time
            logger.error("Query %s failed after %.2fs: %s", query_id, processing_time, exc, exc_info=True)
            raise Exception(f"RAG processing failed: {exc}") from exc

        processing_time = time.time() - start_time
        return self._to_response(result, processing_time, query_id)

    def _route_divisions(self, state: RAGState) -> dict[str, Any]:
        requested_filter = state.get("divisions_filter")
        if requested_filter:
            return {"selected_divisions": requested_filter}

        valid_divisions = list(self.settings.subcommittee_stores.keys())
        routing_llm = create_chat_model("routing", "routing").with_structured_output(RouteDecision)
        allowed_divisions = "\n- ".join(valid_divisions)
        decision = routing_llm.invoke(
            [
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
        )
        selected = [division for division in decision.divisions if division in self.settings.subcommittee_stores]
        if not selected:
            logger.warning("Router returned no valid divisions; querying all divisions as fallback")
            selected = valid_divisions
        return {"selected_divisions": selected}

    def _fan_out_divisions(self, state: RAGState) -> list[Send]:
        return [
            Send(
                "retrieve_division",
                {
                    "question": state["question"],
                    "division": division,
                    "max_results": state["max_results"],
                },
            )
            for division in state.get("selected_divisions", [])
        ]

    def _retrieve_division(self, state: RAGState) -> dict[str, Any]:
        division = state["division"]  # type: ignore[typeddict-item]
        chunks = self.vectorstores.retrieve(
            question=state["question"],
            division=division,
            k=state["max_results"],
        )
        return {"retrieved_chunks": chunks}

    def _fan_out_chunks(self, state: RAGState) -> dict[str, Any]:
        return {}

    def _send_chunks_to_map(self, state: RAGState) -> list[Send]:
        return [
            Send(
                "map_chunk",
                {
                    "question": state["question"],
                    "chunk": chunk,
                    "thinking_speed": state["thinking_speed"],
                    "model_used": state["model_used"],
                },
            )
            for chunk in state.get("retrieved_chunks", [])
        ]

    def _map_chunk(self, state: RAGState) -> dict[str, Any]:
        chunk: RetrievedChunkState = state["chunk"]  # type: ignore[typeddict-item]
        model = state["model_used"]
        llm = create_chat_model(model, "map")
        question = state["question"]

        extraction_prompt = (
            "You are a legislative financial analyst. Extract only facts from the source chunk "
            "that help answer the question. Preserve dollar figures, fiscal years, agencies, "
            "section references, and quote exact numbers. End facts with the citation marker "
            f"[{chunk['division_acronym']}].\n\n"
            f"Question:\n{question}\n\n"
            f"Source chunk:\n{chunk['content']}"
        )
        summary_prompt = (
            "Write one concise sentence explaining what useful evidence this source chunk contains. "
            "Mention the relevant program, agency, or figure if present.\n\n"
            f"Question:\n{question}\n\n"
            f"Source chunk:\n{chunk['content']}"
        )

        with ThreadPoolExecutor(max_workers=2) as executor:
            facts_future = executor.submit(self._invoke_text, llm, extraction_prompt)
            summary_future = executor.submit(self._invoke_text, llm, summary_prompt)
            extracted_facts = facts_future.result()
            chunk_summary = summary_future.result()

        mapped: MappedChunkState = {
            "chunk_id": chunk["chunk_id"],
            "division": chunk["division"],
            "division_acronym": chunk["division_acronym"],
            "extracted_facts": extracted_facts,
            "chunk_summary": chunk_summary,
            "source_content": chunk["content"],
            "score": chunk.get("score"),
            "metadata": chunk.get("metadata", {}),
        }
        return {"mapped_chunks": [mapped]}

    def _fan_out_reduce_divisions(self, state: RAGState) -> dict[str, Any]:
        return {}

    def _send_divisions_to_reduce(self, state: RAGState) -> list[Send]:
        by_division: dict[str, list[MappedChunkState]] = {}
        retrieved_counts: dict[str, int] = {}

        for chunk in state.get("retrieved_chunks", []):
            retrieved_counts[chunk["division"]] = retrieved_counts.get(chunk["division"], 0) + 1

        for mapped in state.get("mapped_chunks", []):
            by_division.setdefault(mapped["division"], []).append(mapped)

        return [
            Send(
                "reduce_division",
                {
                    "question": state["question"],
                    "division": division,
                    "division_acronym": division_acronym(division),
                    "mapped_items": by_division.get(division, []),
                    "chunks_retrieved": retrieved_counts.get(division, 0),
                    "model_used": state["model_used"],
                },
            )
            for division in state.get("selected_divisions", [])
        ]

    def _reduce_division(self, state: RAGState) -> dict[str, Any]:
        division = state["division"]  # type: ignore[typeddict-item]
        mapped_items: list[MappedChunkState] = state.get("mapped_items", [])  # type: ignore[assignment]
        chunks_retrieved = state.get("chunks_retrieved", 0)
        model = state["model_used"]
        llm = create_chat_model(model, "reduce")

        facts = "\n\n".join(item["extracted_facts"] for item in mapped_items)
        if not facts.strip():
            answer = "No relevant facts found for this division."
        else:
            prompt = (
                "Synthesize the extracted facts into a concise division-level answer. "
                "Preserve all dollar figures and compact citation markers exactly as provided. "
                "Use bullets when helpful.\n\n"
                f"Question:\n{state['question']}\n\n"
                f"Division: {division}\n\n"
                f"Extracted facts:\n{facts}"
            )
            answer = self._invoke_text(llm, prompt)

        division_answer: DivisionAnswerState = {
            "division": division,
            "division_acronym": state["division_acronym"],  # type: ignore[typeddict-item]
            "answer": answer,
            "source_chunk_ids": [item["chunk_id"] for item in mapped_items],
            "chunks_retrieved": chunks_retrieved,
        }
        return {"division_answers": [division_answer]}

    def _synthesize_final(self, state: RAGState) -> dict[str, Any]:
        division_answers = state.get("division_answers", [])
        if not division_answers:
            return {"final_answer": "No answers found."}

        model = state["model_used"]
        llm = create_chat_model(model, "synthesize")
        context = "\n\n".join(
            f"## {item['division']} [{item['division_acronym']}]\n{item['answer']}"
            for item in division_answers
        )
        prompt = (
            "Create the final answer from the division-level answers. "
            "Keep it concise, policy-brief style, numerically precise, and preserve citation markers. "
            "When mentioning figures, keep the citation marker immediately after the figure or clause.\n\n"
            f"Question:\n{state['question']}\n\n"
            f"Division answers:\n{context}"
        )
        return {"final_answer": self._invoke_text(llm, prompt)}

    def _invoke_text(self, llm: Any, prompt: str) -> str:
        response = llm.invoke(prompt)
        content = getattr(response, "content", response)
        if isinstance(content, list):
            return "\n".join(str(block) for block in content)
        return str(content).strip()

    def _to_response(self, result: RAGState, processing_time: float, query_id: str) -> QueryResponse:
        mapped_by_chunk = {chunk["chunk_id"]: chunk for chunk in result.get("mapped_chunks", [])}
        sources = self._source_documents(result, mapped_by_chunk) if result.get("include_sources") else None
        debug_chunks = self._debug_chunks(result, mapped_by_chunk) if result.get("debug_chunks") else None

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
        return [
            SourceDocument(
                division=chunk["division"],
                division_acronym=chunk["division_acronym"],
                chunk_id=chunk["chunk_id"],
                content_snippet=chunk["content"],
                chunk_summary=mapped_by_chunk.get(chunk["chunk_id"], {}).get("chunk_summary"),
                confidence_score=None,
                metadata=chunk.get("metadata", {}),
            )
            for chunk in result.get("retrieved_chunks", [])
        ]

    def _debug_chunks(
        self,
        result: RAGState,
        mapped_by_chunk: dict[str, MappedChunkState],
    ) -> list[DebugChunk]:
        return [
            DebugChunk(
                chunk_id=chunk["chunk_id"],
                division=chunk["division"],
                division_acronym=chunk["division_acronym"],
                content=chunk["content"],
                chunk_summary=mapped_by_chunk.get(chunk["chunk_id"], {}).get("chunk_summary"),
                score=chunk.get("score"),
                metadata=chunk.get("metadata", {}),
            )
            for chunk in result.get("retrieved_chunks", [])
        ]

    async def ingest_data(
        self,
        embedding_model: str,
        clear_existing: bool = True,
        ingest_id: Optional[str] = None,
    ) -> tuple[IngestResponse, str]:
        start_time = time.time()
        ingest_id = ingest_id or f"ingest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        logger.info("Starting ingestion %s with embedding model %s", ingest_id, embedding_model)

        try:
            self.vectorstores.clear_cached_stores()
            divisions_processed = self.ingestion.ingest(embedding_model, clear_existing)
            self.vectorstores.reset_embedding_model(embedding_model)
            self.settings.embedding_model = embedding_model
        except Exception as exc:
            elapsed = time.time() - start_time
            logger.error("Ingestion %s failed after %.2fs: %s", ingest_id, elapsed, exc, exc_info=True)
            raise Exception(f"Ingestion failed after {elapsed:.1f} seconds: {exc}") from exc

        processing_time = time.time() - start_time
        return (
            IngestResponse(
                status="completed",
                message=f"Successfully ingested {divisions_processed} divisions using {embedding_model}",
                embedding_model=embedding_model,
                divisions_processed=divisions_processed,
                processing_time=processing_time,
            ),
            embedding_model,
        )

    async def health_check(self) -> dict[str, str]:
        try:
            vectorstore_dir = str(self.settings.vectorstore_dir)
            available_stores = [
                name
                for name in os.listdir(vectorstore_dir)
                if os.path.isdir(os.path.join(vectorstore_dir, name))
            ]
            if not available_stores:
                return {"status": "unhealthy", "reason": "No vector databases found"}

            return {
                "status": "healthy",
                "database_status": "connected",
                "available_divisions": str(len(available_stores)),
                "embedding_model": self.vectorstores.embedding_model,
            }
        except Exception as exc:
            return {"status": "unhealthy", "reason": f"Database connectivity issue: {exc}"}


_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the process-wide RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
