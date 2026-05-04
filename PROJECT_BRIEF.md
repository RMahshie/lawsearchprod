# LawSearch — Project Brief

> A self-contained briefing on the LawSearch codebase. Paste this as the first
> message of a fresh Claude conversation when you want to discuss the project
> without having to re-explain it.

## 1. What it is

**LawSearch** is a Retrieval-Augmented Generation (RAG) web app for asking
natural-language questions about U.S. federal appropriations bills (currently
FY2026: P.L. 119-37, 119-74, and 119-75).

The product's distinguishing feature is **fully cited answers**: every visible
dollar figure in an answer is bound to a structured Number Annotation that
either points at a single source chunk of bill text (Source-backed Figure) or
documents an equation over other annotations (Derived Figure). Hovering a
figure in the UI shows the chunk it came from, or the math used to derive it.

Solo project. Currently deployed to Railway with a Postgres saved-question DB
and a bind-mounted ChromaDB on local disk.

## 2. Stack

- **Backend:** FastAPI + Pydantic, LangGraph for the query pipeline, LangChain
  for chat-model abstraction, ChromaDB (persistent) for vector storage,
  OpenAI for embeddings and chat. Python 3.13.
- **Frontend:** React + Vite + TypeScript. shadcn/ui components.
- **Persistence:** Postgres (saved questions, vector store registry) via
  SQLAlchemy + psycopg v3.
- **Deployment:** Docker Compose for local; Railway in production.
- **Streaming:** Server-Sent Events for query progress.

## 3. Domain vocabulary (read this carefully)

The project's `CONTEXT.md` defines this glossary; agents and contributors are
expected to use these terms verbatim. The shorthand definitions below are the
load-bearing ones:

- **Division** — a LawSearch retrieval bucket. The unit the router selects,
  retrieval queries, and the reduce stage summarizes. There are 12 Divisions
  for FY2026 (AG, LEG, MCVA, CJS, EWD, INT, DOD, LHHS, THUD, FSGG, SFOPS,
  CRX). Usually wraps one Bill Division 1:1; CRX is the exception.
- **Bill Division** — Congress's own structural unit, headed "DIVISION X"
  inside a Public Law. Distinct from a LawSearch Division only when multiple
  Bill Divisions are aggregated under one (currently only CRX).
- **CRX** — the "Continuing Resolution Extras" Division. The one synthesized
  Division that aggregates Bill Divisions covering continuing appropriations,
  extenders, Homeland Security, and miscellaneous matter that doesn't belong
  to a single subcommittee. For FY2026 it wraps nine Bill Divisions across
  two Public Laws.
- **Source Part** — a `(public_law, division_letter, division_title,
  source_file)` tuple identifying a slice of bill text. A Division is composed
  of one or more Source Parts; only CRX has more than one.
- **Division Acronym** — stable short marker (DOD, CRX, LHHS, etc.). Used in
  citations and embedded in `chunk_id`s; load-bearing, not just a UI label.
- **Chunk** — an immutable slice of bill text embedded into a Division's
  vector store, addressed by a stable `chunk_id`. The id format encodes the
  Division Acronym so chunks survive rebuilds and can be rehydrated when
  serving citations.
- **Chunk Summary** — one-line LLM-generated sentence describing what a Chunk
  says. Used in citation hover UI.
- **Chunk Snapshot** — short LLM-generated label (a few words) naming what a
  Chunk is about. Used as the row title in source excerpt lists. Distinct
  from a Chunk Summary — snapshot is a title, summary is a sentence.
- **Number Annotation** — structured provenance for a single visible dollar
  figure in an answer. Either a Source-backed Figure or a Derived Figure.
- **Source-backed Figure** — a Number Annotation traceable to a single Chunk;
  the figure appears verbatim in bill text. Atomic; not computed.
- **Derived Figure** — a Number Annotation produced by combining other
  annotations via a stated equation. Carries a short non-chain-of-thought
  rationale, never a reasoning trace.
- **Annotation Marker** — the inline `[[num:ID]]` link inside answer markdown
  that ties a visible figure to its Number Annotation. Markers can appear in
  the top-level answer or inside a Division summary.
- **Thinking Speed** — user-selected pipeline strategy (`quick` / `normal` /
  `long`) that controls per-stage model selection and retrieval parameters.
  Different stages may use different OpenAI models within one mode.
- **Saved Question** — persisted record of one Q&A plus citation pointers
  (chunk_id, rank, summary, snapshot). Source text is **not** stored — it is
  fetched from Chroma on view via Rehydrate. The codebase's API still calls
  this a "Conversation" (single Q&A, not multi-turn) — that name is a
  flagged ambiguity; prefer "Saved Question" in design discussion.
- **Vector Store Root** — versioned filesystem root containing a built set of
  Chroma stores (one subdirectory per Division). A Saved Question records the
  Vector Store Root it was built against; if that root is rebuilt or removed,
  some of its Chunks may fail to rehydrate.
- **Rehydrate** — looking up a Chunk's source text and metadata in Chroma at
  view time using `(vector_store_root, division, chunk_id)`. Missing chunks
  are silently skipped — a Saved Question stays viewable, just thinner.
- **Routing Alias** — a free-text hint string per Division listing agencies,
  programs, and keywords that should pull that Division into the Route stage's
  selection. Editorial artifact; lives in `app/core/config.py`.

## 4. The Query Pipeline (six stages)

A LangGraph state graph turns a question into an answer:

```
START -> classify_answer_mode -> route_divisions -> rewrite_division_queries
      -> Send retrieve_division -> fan_out_chunks -> Send map_chunk
      -> fan_out_reduce_divisions -> Send reduce_division
      -> synthesize_final -> END
```

The named stages, in order:

1. **Classify** — pick the answer shape (`direct_account_amount`,
   `broad_topic_total`, `funding_mechanism_no_amount`,
   `reconciliation_breakdown`, `general_summary`).
2. **Route** — pick which Divisions to query. Bypassed when the request
   supplies an explicit `divisions_filter`. If no Division matches, the
   pipeline short-circuits with an "incompatible question" answer.
3. **Rewrite** — for each selected Division, rewrite the user's question into
   a Division-tailored retrieval query. DOD's store gets queried with a
   DOD-tailored phrasing, LHHS's with LHHS phrasing, etc.
4. **Retrieve** — for each selected Division, pull the top-`k` Chunks from
   that Division's vector store using its rewritten query.
5. **Map** — for each retrieved Chunk, two LLM calls: extract structured
   facts (figures, agencies, programs; tagged direct/adjacent/not_responsive)
   and produce a one-line Chunk Summary plus a short Chunk Snapshot.
6. **Reduce** — for each Division, fold its mapped Chunks into a single
   Division-level answer with Annotation Markers.
7. **Synthesize** — combine all Division answers into the final cross-Division
   answer. Validates Derived Figure proposals against displayed-figure parsing
   and input-sum arithmetic before accepting them.

The fan-out steps use LangGraph `Send` to parallelize: Retrieve runs once per
selected Division concurrently, Map runs once per retrieved Chunk concurrently
(within a chunk: facts/summary/snapshot also run in parallel via a
`ThreadPoolExecutor`), Reduce runs once per Division concurrently.

## 5. Key invariants

- `divisions_filter` bypasses Route entirely.
- `max_results` means Chunks per selected Division.
- Every retrieved/mapped Chunk and Division answer carries `division` and
  `division_acronym`.
- State reducers append flat lists; grouping by Division happens inside the
  fan-out/reduce nodes.
- Every visible dollar figure in an answer **must** be bound to a Number
  Annotation. Never emit a figure without one.
- Source-backed Figures point to a single `chunk_id`. Derived Figures carry
  an equation and `input_ids`; the validator rejects derived proposals whose
  equation arithmetic doesn't match the displayed marker figure or whose
  inputs aren't all source-resolvable.
- Saved Questions store citation pointers, never source text.
- `chunk_id`s are deterministic across rebuilds (`Acronym-N-hash`). Do not
  invent fallback ids — that breaks rehydration silently.

## 6. Code layout

The query pipeline lives in `app/services/rag/`:

```
app/services/rag/
├── __init__.py            # public re-exports
├── service.py             # RAGService class (graph wiring, process_query,
│                          # ingest_data, health_check, progress streaming)
├── context.py             # RAGContext dataclass passed to stage functions
├── state.py               # LangGraph TypedDicts, FIGURE_PATTERN, NUMBER_MARKER_PATTERN
├── schemas.py             # Pydantic schemas for structured LLM outputs
├── stages/
│   ├── classify.py        # answer-mode classification
│   ├── route.py           # division selection
│   ├── rewrite.py         # per-Division query rewriting
│   ├── retrieve.py        # Chroma retrieval
│   ├── map_chunk.py       # facts + summary + snapshot per chunk
│   ├── reduce.py          # Division-level answer fold
│   └── synthesize.py      # cross-Division final answer
├── annotations.py         # Number Annotation pipeline (source extraction,
│                          # marker insertion, derived validation, dollar
│                          # parsing, ID generation)
├── relevance.py           # mapped-fact tier bookkeeping
├── llm_invocation.py      # invoke_with_retry, invoke_text, invoke_structured_or_text
└── response.py            # QueryResponse shaping
```

`app/services/rag_service.py` is a backwards-compatible shim that re-exports
`RAGService`, `get_rag_service`, and the structured-LLM schemas. External code
should import from there, not from the package internals directly.

Stage functions are pure: they take `(state, ctx)` where `ctx` is a
`RAGContext` (settings, vectorstores, emit_progress, debug_log). `RAGService`
methods are thin wrappers that build a fresh `ctx` via `self._make_ctx()` on
each call.

Other relevant files:

- `app/core/config.py` — Pydantic settings, the FY2026 division/store map,
  routing aliases, source-part manifest.
- `app/api/endpoints/query.py` — `/api/query`, `/api/query/stream` (SSE),
  `/api/health`, `/api/status`.
- `app/api/endpoints/storage.py` — vector store CRUD and Saved Question
  endpoints.
- `app/services/llm_factory.py` — the Thinking Speed strategy table; resolves
  which OpenAI model + reasoning_effort each stage uses.
- `app/services/rag_prompting.py` — answer-mode-aware map/reduce/synthesis
  prompt builders.
- `app/services/vector_store_service.py` — Chroma access, chunk shaping.
- `app/services/ingestion_service.py` — rebuilds Chroma stores from bill HTML.
- `app/services/storage_registry.py` — vector store registry + Saved Question
  persistence + load_conversation rehydration.
- `app/db/models.py` — SQLAlchemy models.
- `frontend/src/types/api.ts` — TypeScript mirror of the backend API.
- `frontend/src/services/api.ts` — Axios client + SSE reader.

## 7. Accepted design decisions (ADRs)

The repo has 8 accepted ADRs in `docs/adr/`. One-sentence summaries:

1. **Saved Questions store citation pointers, not source text.** Pointers
   stay valid across re-ingest; missing chunks are skipped, not errored.
2. **Per-Division Chroma stores.** 12 stores, one per Division, instead of a
   single store with a `division` metadata filter. Enables parallel retrieval
   and narrow scope per query.
3. **CRX as a synthesized Division.** Aggregates 9 Bill Divisions across 2
   Public Laws so routing has enough surface area to work reliably on small
   extender/continuation matter.
4. **Six-stage map-reduce graph instead of `RetrievalQA`.** Required for
   per-Division observability, structured outputs, and the Number Annotation
   pipeline.
5. **Thinking Speed is a per-stage strategy, not a single-knob mode.** Map
   uses cheaper models, Synthesize uses stronger ones, hand-tuned by mode.
6. **Number Annotations come from structured LLM output, not regex.** Forces
   the model to commit to a chunk citation or an equation at emit time;
   regex post-processing can't tell two identical figures apart.
7. **Per-Division query rewrite stage exists at all.** Avoids noisy retrieval
   on cross-Division questions where the relevant content lives in different
   forms across Divisions.
8. **Deterministic `chunk_id`s that survive rebuilds.** Required by ADR-0001;
   without them every rebuild orphans Saved Questions.

## 8. Persistence model

Two storage layers:

- **Chroma stores** (per-Division, on disk under `db/chroma/<vector_store_root>/<division_dir>/`):
  the source of truth for Chunk content and embeddings. Rebuilt by
  `ingestion_service.py`.
- **Postgres** (when `DATABASE_URL` is set; SQLite fallback for local dev):
  vector store registry (which roots exist, which is active), Saved
  Questions, and citation pointers. The DB never stores Chunk content; it
  references Chunks by `(vector_store_id, division, chunk_id)`.

`storage_registry.load_conversation(db, query_id, chunk_loader)` rebuilds a
saved Q&A by joining DB rows with chunk_loader results from Chroma. Missing
chunks are skipped rather than erroring.

## 9. API surface

- `POST /api/query` — submit a query, get a `QueryResponse` (final answer,
  selected Divisions, per-Division results, sources, Number Annotations,
  timing, query id, Thinking Speed, model used).
- `POST /api/query/stream` — same, but streams progress via SSE. Stages emit
  events: `start`, `classifying`, `routing`, `rewriting`, `retrieving`,
  `mapping`, `reducing`, `synthesizing`, `done`. Final `result` event carries
  the full `QueryResponse`.
- `GET /api/health`, `GET /api/status` — health/diagnostic endpoints.
- `GET /api/conversations`, `GET /api/conversations/{id}` — list/load Saved
  Questions (called "conversations" in the API per the noted ambiguity).
- Vector store CRUD lives under `/api/storage/vector-stores`.

`QueryRequest` accepts: `question`, `thinking_speed` (`quick|normal|long`),
`max_results` (Chunks per Division), `include_sources`, `divisions_filter`.

## 10. How to talk about this project

If you (web Claude) want to suggest changes or discuss design choices:

- Use the vocabulary in section 3 verbatim. Do not invent synonyms.
- Treat the 8 ADRs as load-bearing. Do not contradict an accepted ADR
  without explicitly proposing a replacement.
- The single biggest distinctive piece is the Number Annotation pipeline —
  every dollar figure must be bound to a structured annotation, with strict
  validation (marker presence, displayed-figure parsing, equation arithmetic,
  source-input resolvability).
- "Conversation" in the persistence layer means Saved Question (single Q&A).
  Do not assume multi-turn chat semantics.
- The pipeline is six stages with a Rewrite step between Route and Retrieve;
  this matters because earlier docs sometimes show a five-stage flow without
  Rewrite.
- For solo-project work cadence: tests are mocked, real query smoke tests
  require `OPENAI_API_KEY` and populated Chroma stores. There's no CI that
  blocks merges; correctness comes from `npm test` (pytest under the hood)
  plus manual SSE smoke testing.
