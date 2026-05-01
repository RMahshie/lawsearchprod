# Code Review Cleanup

## Goal
Implement the cleanup items found in the code review: make manual division filters truly bypass routing, honor `include_sources`, restore or remove dead debug query wiring, remove unused frontend query paths, reduce duplicated API client/error handling, reduce duplicated structured-output invocation code, prune unused compatibility helpers, and resolve the half-wired embedding model UI/API split.

## Non-Goals
Do not change RAG prompt behavior, model strategy, vector-store ingestion semantics, saved-history hydration, or number-provenance behavior beyond the reviewed cleanup items.

## Current Behavior
Manual division filters still invoke the routing LLM before returning the requested divisions. `include_sources` is exposed but ignored by backend state initialization. Debug division query data is modeled and rendered but never returned. The frontend keeps an unused non-stream query path and duplicated axios interceptor logic. Backend structured-output calls duplicate fallback flow. Several compatibility helpers have no internal call sites. Embedding model CRUD is partly exposed but the UI uses static model options.

## Proposed Behavior
Manual filters bypass the router before any router model work. `include_sources` controls response source inclusion. Debug division queries are returned only in debug mode. The frontend uses one streamed query path and shared API client error handling. Structured-output invocation uses one shared helper with clearer fallback behavior. Unused compatibility helpers are removed when not imported. Embedding model choices are dynamic from the API and the unused create-model path is removed.

## Relevant Files
app/services/rag_service.py
app/models/query.py
app/api/endpoints/storage.py
app/models/storage.py
app/db/session.py
app/core/config.py
app/core/__init__.py
frontend/src/services/api.ts
frontend/src/hooks/useApi.ts
frontend/src/App.tsx
frontend/src/types/api.ts
tests/test_rag_service_units.py
tests/test_query_models.py

## Assumptions
The stream query path is the only supported frontend query path.
Debug division queries should remain available when `DEBUG=true`.
Embedding model selection should use registered backend models rather than hardcoded frontend-only constants.

## Open Questions
None. The user approved implementing all proposed updates.

## Execution Steps
- [x] Update backend RAG request behavior and debug-query response wiring.
- [x] Consolidate structured-output invocation fallback helpers.
- [x] Remove unused backend compatibility helpers and half-wired create-embedding-model endpoint/model.
- [x] Clean frontend API clients/hooks and switch embedding selection to dynamic API data.
- [x] Update tests for changed behavior.
- [x] Run backend tests and frontend build.

## Validation
python3 -m pytest tests/test_rag_service_units.py tests/test_query_models.py tests/test_ingestion_service.py
npm run build:frontend

## Documentation
No docs expected unless API surface changes require it. Removing unused create-embedding-model POST may require updating docs only if it is documented.

## Progress
2026-05-01 03:05 EDT - Plan written after code review and user approval to implement all updates.
2026-05-01 03:05 EDT - Backend request behavior, debug output, structured invocation helper, compatibility cleanup, frontend API cleanup, and dynamic embedding model UI updates implemented.
2026-05-01 03:05 EDT - Validation passed: backend focused pytest suite and frontend production build.

## Decisions
Return debug division queries only when `settings.debug` is true, keeping normal responses compact while making existing debug UI functional.
Prefer dynamic GET-backed embedding models in the UI and remove the unused POST/create path.

## Discoveries
The existing frontend was already fully on the streaming query path, so the non-stream React Query mutation/cache path could be removed without replacing any UI caller.

## Remaining Work
None.
