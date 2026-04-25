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
    selected_divisions: list[str]
    division_queries: list[DivisionQueryState]
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
        self._progress_callbacks: dict[str, Callable[[dict[str, Any]], None]] = {}
        self._progress_lock = Lock()
        self._graph = self._build_graph()

    def _build_graph(self):
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
        start_time = time.time()
        query_id = query_id or f"query_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        thinking_speed = request.thinking_speed or "normal"
        model_used = describe_model_strategy(thinking_speed)
        if progress_callback:
            with self._progress_lock:
                self._progress_callbacks[query_id] = progress_callback

        state: RAGState = {
            "query_id": query_id,
            "question": request.question,
            "thinking_speed": thinking_speed,
            "max_results": retrieval_k_for_request(request),
            "include_sources": bool(request.include_sources),
            "debug_chunks": bool(request.debug_chunks),
            "divisions_filter": request.divisions_filter,
            "model_used": model_used,
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
        return self._to_response(result, processing_time, query_id)

    def _route_divisions(self, state: RAGState) -> dict[str, Any]:
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
            plan = rewrite_llm.invoke(
                [
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
        start_time = time.time()
        division = state["division"]  # type: ignore[typeddict-item]
        self._emit_progress(
            state,
            "retrieving",
            "Searching source text",
            division=division_acronym(division),
        )
        chunks = self.vectorstores.retrieve(
            question=state.get("retrieval_query", state["question"]),  # type: ignore[typeddict-item]
            division=division,
            k=state["max_results"],
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
        return {}

    def _send_chunks_to_map(self, state: RAGState) -> list[Send]:
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
            "Write exactly one plain-English sentence for a UI hover summary. "
            "State what useful evidence this chunk contains, mentioning the main agency, program, "
            "account, or dollar figure if present. Do not use bullets and do not introduce new facts.\n\n"
            f"Question:\n{question}\n\n"
            f"Source chunk:\n{chunk['content']}"
        )

        with ThreadPoolExecutor(max_workers=2) as executor:
            facts_future = executor.submit(self._invoke_text, map_llm, extraction_prompt)
            summary_future = executor.submit(self._invoke_text, summary_llm, summary_prompt)
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
        self._debug_log(
            "map query_id=%s chunk_id=%s division=%s map_model=%s summary_model=%s duration=%.2fs facts_chars=%s summary_chars=%s",
            state.get("query_id", "unknown"),
            chunk["chunk_id"],
            chunk["division_acronym"],
            format_model_spec(map_model),
            format_model_spec(summary_model),
            time.time() - start_time,
            len(extracted_facts),
            len(chunk_summary),
        )
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
            answer = self._invoke_text(llm, prompt)

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
        final_answer = self._invoke_text(llm, prompt)
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

    def _invoke_text(self, llm: Any, prompt: str) -> str:
        response = llm.invoke(prompt)
        content = getattr(response, "content", response)
        if isinstance(content, list):
            return "\n".join(str(block) for block in content)
        return str(content).strip()

    def _debug_log(self, message: str, *args: Any) -> None:
        """Emit concise RAG timing traces only when DEBUG=true."""
        if getattr(getattr(self, "settings", None), "debug", False):
            logger.info("RAG_DEBUG " + message, *args)

    def _emit_progress(self, state_or_query_id: RAGState | str, stage: str, message: str, **details: Any) -> None:
        """Emit query progress to an optional streaming callback."""
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

    def _debug_division_queries(self, result: RAGState) -> list[DebugDivisionQuery]:
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
        chunk_size: int | None = None,
        clear_existing: bool = True,
        ingest_id: Optional[str] = None,
    ) -> tuple[IngestResponse, str]:
        start_time = time.time()
        ingest_id = ingest_id or f"ingest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        logger.info("Starting ingestion %s with embedding model %s", ingest_id, embedding_model)

        try:
            self.vectorstores.clear_cached_stores()
            divisions_processed = self.ingestion.ingest(embedding_model, clear_existing, chunk_size)
            self.vectorstores.reset_embedding_model(embedding_model)
            self.settings.embedding_model = embedding_model
            if chunk_size:
                self.settings.chunk_size = chunk_size
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
                chunk_size=chunk_size or self.settings.chunk_size,
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
