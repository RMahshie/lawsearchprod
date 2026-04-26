# LawSearch AI

RAG app for querying 2024 U.S. federal appropriations bills. Stack: FastAPI backend, LangGraph/LangChain, ChromaDB, OpenAI, React/Vite/TypeScript frontend, Docker Compose.

## Commands

```bash
npm run dev                 # backend + frontend
npm run dev:backend         # FastAPI on :8000
npm run dev:frontend        # Vite frontend
npm test                    # backend pytest suite
npm run build:frontend      # frontend typecheck + build
docker-compose up --build   # full stack containers
```

Use `python3`, not bare `python`, in this environment. Required env: `OPENAI_API_KEY`. Optional: `EMBEDDING_MODEL`, `API_HOST`, `API_PORT`, `LOG_LEVEL`, `ENVIRONMENT`.

## Key Files

- `app/main.py`: FastAPI app and router registration.
- `app/api/endpoints/query.py`: `/api/query`, `/api/query/stream`, `/api/health`, `/api/status`.
- `app/api/endpoints/storage.py`: storage manager and saved question history endpoints.
- `app/models/query.py`: Pydantic API contract.
- `app/services/rag_service.py`: LangGraph query orchestration.
- `app/services/vector_store_service.py`: Chroma access and chunk IDs/acronyms.
- `app/services/llm_factory.py`: thinking-speed and OpenAI model selection.
- `app/services/ingestion_service.py`: rebuilds Chroma stores from bill HTML.
- `app/core/config.py`: settings and 14-division store mapping.
- `frontend/src/types/api.ts`: frontend mirror of backend API models.

## Current RAG Flow

`START -> route_divisions -> Send retrieve_division -> fan_out_chunks -> Send map_chunk -> fan_out_reduce_divisions -> Send reduce_division -> synthesize_final -> END`

Important invariants:
- `divisions_filter` bypasses routing.
- `max_results` means chunks per selected division.
- Every retrieved chunk, mapped chunk, and division answer carries `division` and `division_acronym`.
- State reducers append flat lists; grouping by division happens inside fan-out/reduce nodes.
- `map_chunk` makes two LLM calls per chunk: extracted facts and one-line `chunk_summary`.
- Sources are first-class response fields for citation hover UI.
- Saved history stores source `chunk_id`, `rank`, `chunk_summary`, and `chunk_snapshot`, not source text.
- Saved history rehydrates source text from Chroma using `vector_store_id + chunk_id`; missing chunks are skipped.

## API Behavior

`QueryRequest` supports `question`, `thinking_speed`, `max_results`, `include_sources`, and `divisions_filter`.

`QueryResponse` includes final answer, selected divisions, per-division results, sources, timing, query id, thinking speed, and model used.

## Frontend Direction

Frontend is still simple. Planned redesign uses shadcn/ui with low-radius, blocky components, restrained black/white/neutral semantic colors, richer query controls, source drilldowns, and figure hover citations backed by returned chunks.

## Gotchas

- Do not reintroduce legacy `RetrievalQA(map_reduce)` or `langchain_classic` chains.
- Do not rely on a `src/ingest.py`; ingestion now lives in `app/services/ingestion_service.py`.
- Existing Chroma stores live under `db/chroma/`; source bills live under `data/bills/`.
- Tests intentionally mock LLM/vector behavior; real query smoke tests require `OPENAI_API_KEY` and populated Chroma stores.
