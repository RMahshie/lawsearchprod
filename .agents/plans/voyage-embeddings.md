# Voyage Embeddings

## Goal
Add Voyage AI as an additional embedding provider for LawSearch Vector Stores, while preserving existing OpenAI embedding support and Saved Question behavior.

## Non-Goals
- Do not replace OpenAI embeddings or change the default Embedding Model.
- Do not add Voyage contextualized chunk embeddings.
- Do not change chunking strategy.
- Do not change Docker Compose environment loading beyond documentation unless implementation proves it is required.
- Do not add a database migration for provider-specific embedding options.

## Current Behavior
Ingestion and retrieval construct `OpenAIEmbeddings` directly from a single `embedding_model` string. The storage registry seeds only OpenAI embedding rows. The Storage Manager lists enabled `EmbeddingModel` rows and sends the selected row id as `embedding_model` when creating a Vector Store.

`EmbeddingModel` already has `id`, `name`, `provider`, `dimensions`, and `is_enabled`, but runtime code mostly treats `embedding_model` as an OpenAI model id. A Vector Store persists `embedding_model_id`, and `.embedding_model` stores the same id for restart-safe retrieval.

## Proposed Behavior
LawSearch treats an **Embedding Model** as a registered provider configuration. The config id remains the value persisted on Vector Stores and in `.embedding_model`; the row `name` is the provider model name.

Add two Voyage Embedding Models alongside existing OpenAI models:
- `id="voyage-law-2"`, `name="voyage-law-2"`, `provider="voyage"`, `dimensions=1024`
- `id="voyage-4-large-2048"`, `name="voyage-4-large"`, `provider="voyage"`, `dimensions=2048`

Use the official `voyageai` client through a small LangChain-compatible wrapper owned by this codebase. Voyage ingestion uses `input_type="document"`. Voyage query retrieval uses `input_type="query"`. Voyage document embedding batches are hard-coded at 64 texts per request. `truncation=True` and `output_dtype="float"`.

`VOYAGE_API_KEY` is optional at app startup. Voyage Embedding Models remain listed, but the Storage Manager greys them out when `VOYAGE_API_KEY` is not configured via a dynamic `is_available` API field. The create-Vector-Store API rejects unavailable models with `400 embedding_model_unavailable` before ingestion starts. Querying an active Voyage-backed Vector Store without `VOYAGE_API_KEY` fails clearly and never falls back to OpenAI.

## Relevant Files
- `CONTEXT.md`
- `docs/adr/0009-embedding-models-are-provider-configurations.md`
- `requirements.txt`
- `app/core/config.py`
- `app/db/models.py`
- `app/models/storage.py`
- `app/services/embedding_factory.py`
- `app/services/storage_registry.py`
- `app/services/ingestion_service.py`
- `app/services/vector_store_service.py`
- `app/api/endpoints/storage.py`
- `frontend/src/types/api.ts`
- `frontend/src/App.tsx`
- `.env.example`
- `docs/SETUP.md`
- `AGENTS.md`
- `tests/test_rag_service_units.py`
- `tests/test_ingestion_service.py`
- `tests/test_query_models.py`

## Assumptions
- `VOYAGE_API_KEY` is the only supported environment variable name for Voyage credentials.
- Existing OpenAI Embedding Models remain available.
- The default Embedding Model remains `text-embedding-3-large`.
- `EmbeddingModel.name` can be used as the provider model name without adding a new DB column.
- Provider-specific config can live in a code registry for now.
- `.embedding_model` should continue storing only the LawSearch config id.

## Open Questions
None. User resolved:
- Initial Voyage models are `voyage-law-2` and max-quality `voyage-4-large` at 2048 dimensions.
- Use config id `voyage-4-large-2048`; display name remains `voyage-4-large`.
- Keep dropdown labels as model names only.
- Grey out unavailable Voyage models when no API key exists.
- Use standard Voyage embeddings, not contextualized chunk embeddings.

## Execution Steps
- [x] Add `voyageai` dependency and optional `voyage_api_key` setting.
- [x] Add `app/services/embedding_factory.py` with OpenAI and Voyage config registry, availability checks, and embedder construction.
- [x] Replace direct `OpenAIEmbeddings` construction in ingestion and vector-store retrieval with the embedding factory.
- [x] Seed Voyage Embedding Model rows with provider/name/dimensions and keep OpenAI rows.
- [x] Extend `EmbeddingModelInfo` with dynamic `is_available`.
- [x] Update storage endpoints to expose availability and reject unavailable model creation with a 400 error before ingestion.
- [x] Update frontend types and Storage Manager dropdown to disable unavailable models while still showing names only.
- [x] Update docs for optional `VOYAGE_API_KEY`.
- [x] Add unit tests for registry seeding, availability, API rejection, Voyage wrapper behavior via mocks, and clear query errors.
- [x] Commit docs/context/ADR changes together with implementation as one Voyage embedding provider change.

## Validation
- `python3 -m pytest tests/test_rag_service_units.py -k "embedding_factory or voyage or seed_embedding_models or unavailable_embedding_model or query_error_message"`: passed.
- `python3 -m pytest tests/test_rag_service_units.py tests/test_ingestion_service.py tests/test_query_models.py`: 65 passed, 1 failed on unrelated DeepSeek profile expectation (`resolve_model("quick", "map").reasoning_effort == "high"` while current code returns `None` for `deepseek-v4-flash`).
- `npm run build:frontend`: passed with existing Vite font-resolution/chunk-size warnings.
- `git diff --check`: passed.
- Manual smoke after user provides/keeps `VOYAGE_API_KEY`: create a Voyage-backed Vector Store, activate it, run a query, confirm retrieval does not use OpenAI embeddings.
- Manual negative smoke without `VOYAGE_API_KEY`: Voyage models disabled in UI; direct API create request returns `400 embedding_model_unavailable`.

## Documentation
- `CONTEXT.md`: add/keep **Embedding Model** definition.
- `docs/adr/0009-embedding-models-are-provider-configurations.md`: record config id vs provider model name decision.
- `.env.example`, `docs/SETUP.md`, and `AGENTS.md`: document optional `VOYAGE_API_KEY`.

## Progress
- 2026-05-06: Grill session resolved Embedding Model terminology and Voyage integration behavior.
- 2026-05-06: Updated `CONTEXT.md` with **Embedding Model** definition.
- 2026-05-06: Added ADR 0009 for Embedding Models as provider configurations.
- 2026-05-06: Wrote execution plan.
- 2026-05-06: Implemented embedding factory, Voyage wrapper, storage availability API, frontend disabled-state handling, and docs updates.
- 2026-05-07: Added clear query error handling for active Voyage-backed Vector Stores when `VOYAGE_API_KEY` is missing.
- 2026-05-07: Targeted Voyage tests and frontend build pass. Broader focused backend suite has one unrelated DeepSeek strategy assertion failure in `test_deepseek_model_strategy_resolves_by_speed_and_task`.

## Decisions
- Embedding Model id is the LawSearch config id; name is the provider model name.
- Voyage initial models: `voyage-law-2` and `voyage-4-large-2048`.
- `voyage-4-large-2048` uses provider model `voyage-4-large` with 2048 dimensions.
- Keep `.embedding_model` as config id only.
- Keep current default Embedding Model.
- Use official `voyageai` client via a local LangChain-compatible wrapper.
- Hard-code Voyage document batch size to 64.
- Use `input_type="document"` for ingestion and `input_type="query"` for retrieval.
- `VOYAGE_API_KEY` optional at startup, required on Voyage use.
- Use dynamic `is_available` for UI grey-out instead of mutating persisted `is_enabled`.
- Reject unavailable embedding model creation with 400 before ingestion.

## Discoveries
- Existing DB model already has `EmbeddingModel.provider` and `dimensions`, which supports adding provider configs without a migration.
- Current runtime construction of embedders is duplicated in ingestion and vector store services.
- LangChain has a Python Voyage package, but current public docs do not clearly show support for both required `input_type` and `output_dimension`; a small local wrapper is safer.

## Remaining Work
- Optional manual smoke after a real `VOYAGE_API_KEY` is available: create a Voyage-backed Vector Store, activate it, run a query, and confirm retrieval uses the Voyage-backed store.
- Unrelated DeepSeek model-strategy test mismatch remains for a separate workstream.
