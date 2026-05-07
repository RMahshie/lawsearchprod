# LawSearch AI

RAG app for querying U.S. federal appropriations bills (FY2026: P.L. 119-37, 119-74, 119-75). Stack: FastAPI backend, LangGraph/LangChain, ChromaDB, OpenAI, React/Vite/TypeScript frontend, Docker Compose.

## Read first

- `CONTEXT.md` — domain glossary (Division, Chunk, Source-backed Figure, Thinking Speed, etc.). Use these terms verbatim; do not introduce synonyms.
- `docs/adr/` — accepted design decisions. Do not contradict an accepted ADR without proposing a replacement ADR first.

## Commands

```bash
npm run dev                 # backend + frontend
npm run dev:backend         # FastAPI on :8000
npm run dev:frontend        # Vite frontend
npm test                    # backend pytest suite
npm run build:frontend      # frontend typecheck + build
docker-compose up --build   # full stack containers
```

Use `python3`, not bare `python`, in this environment. Required env: `OPENAI_API_KEY`. Optional env: `DEBUG`, `VOYAGE_API_KEY` for Voyage-backed vector stores.

## Query Pipeline

Six-stage LangGraph state graph (see `CONTEXT.md` for stage definitions, ADR-0004 for why):

`START -> route_divisions -> rewrite_division_queries -> Send retrieve_division -> fan_out_chunks -> Send map_chunk -> fan_out_reduce_divisions -> Send reduce_division -> synthesize_final -> END`

(`classify_answer_mode` runs first to pick the answer shape, before `route_divisions`.)

## Code Layout

The pipeline implementation lives in the `app/services/rag/` package:

- `service.py` — `RAGService` class (graph wiring, `process_query`, `ingest_data`, `health_check`, progress streaming).
- `context.py` — `RAGContext` dataclass passed to pure stage functions.
- `state.py` — LangGraph `TypedDict` state shapes plus shared regex constants.
- `schemas.py` — Pydantic schemas for structured LLM outputs.
- `stages/{classify,route,rewrite,retrieve,map_chunk,reduce,synthesize}.py` — one Query Pipeline stage per file. Each exposes pure functions taking `(state, ctx)`.
- `annotations.py` — Number Annotation pipeline (source extraction, marker insertion, derived validation, dollar parsing, ID generation).
- `relevance.py` — Mapped-fact relevance bookkeeping.
- `llm_invocation.py` — `invoke_with_retry`, `invoke_text`, `invoke_structured_or_text`.
- `response.py` — `QueryResponse` shaping helpers.

`app/services/rag_service.py` is a backwards-compatible shim re-exporting `RAGService`, `get_rag_service`, and the structured-LLM schemas. Do not import the implementation modules from outside `app/services/rag/` — go through the shim or `app/services/rag/__init__.py`.

## Invariants

- `divisions_filter` bypasses Route.
- `max_results` means Chunks per selected Division.
- Every retrieved Chunk, mapped Chunk, and Division answer carries `division` and `division_acronym`.
- State reducers append flat lists; grouping by Division happens inside fan-out/reduce nodes.
- Every visible dollar figure in an answer MUST be bound to a Number Annotation (Source-backed or Derived). Never emit a figure without one. See ADR-0006.
- Source-backed Figures point to a single `chunk_id`; Derived Figures carry an equation and `input_ids`.
- Sources are first-class response fields for citation hover UI.
- Saved Questions store citation pointers (`chunk_id`, `rank`, `chunk_summary`, `chunk_snapshot`), never source text. Source text is fetched via Rehydrate against the recorded Vector Store Root. Missing Chunks are skipped silently. See ADR-0001.
- `chunk_id`s are deterministic across rebuilds (Acronym + index + content hash). Do not invent fallback ids. See ADR-0008.

## API Behavior

`QueryRequest` supports `question`, `thinking_speed`, `max_results`, `include_sources`, and `divisions_filter`.

`QueryResponse` includes final answer, selected Divisions, per-Division results, sources, timing, query id, Thinking Speed, and model used.

Note: the persistence API uses "Conversation" for what is actually a Saved Question (single Q&A, not multi-turn). See `CONTEXT.md` flagged ambiguities. Prefer the domain term in design discussion; keep the API name as-is.

## Execution Plans

For complex features, refactors, migrations, or ambiguous multi-file changes, create an Execution Plan using `.agents/PLANS.md`.

Create task-specific plans under `.agents/plans/`.

Do not implement until the plan is written and approved.

While implementing, keep the plan updated with progress, decisions, discoveries, validation, and remaining work.

## Commit Workflow

As sections of work are completed, create small, logical commits that bundle the related file changes together so the history is easy to review.

Do not add assistant attribution, generated-by tags, or co-author trailers to commits.

## Gotchas

- Do not reintroduce legacy `RetrievalQA(map_reduce)` or `langchain_classic` chains. See ADR-0004.
- Do not rely on a `src/ingest.py`; ingestion now lives in `app/services/ingestion_service.py`.
- Existing Chroma stores live under `db/chroma/`; source bills live under `data/bills/`.
- Tests intentionally mock LLM/vector behavior; real query smoke tests require `OPENAI_API_KEY` and populated Chroma stores.
- Do not add silent fallbacks for required runtime state. Fallbacks are useful only when the substitute preserves the same contract; otherwise fail loudly with a clear error and debug context. Example: retrieval must use the active Vector Store Root and persisted `chunk_id`s. Falling back to a legacy root or inventing fallback chunk ids can make live results appear to work while saved-question Rehydration and citation popovers break later.
