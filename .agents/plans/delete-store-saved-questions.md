# Delete Store Saved Questions

## Goal
Make deleting an inactive Vector Store also delete all Saved Questions that reference that Vector Store, so old stores can be removed without hidden `409 store_referenced` failures.

## Non-Goals
- Do not allow deleting the active Vector Store.
- Do not preserve Saved Questions after their backing Vector Store is deleted.
- Do not add a separate Saved Question deletion feature.
- Do not change ingestion, activation, retrieval, citation hydration, or Vector Store creation behavior.
- Do not add database migrations unless implementation proves existing ORM deletes are insufficient.

## Current Behavior
The backend delete endpoint for `DELETE /api/storage/vector-stores/{store_id}` refuses to delete:
- active Vector Stores with `400 store_active`
- inactive Vector Stores referenced by Saved Questions with `409 store_referenced`, unless `force=true`

The frontend delete button only disables active stores. It calls `deleteVectorStore(store.id)` without `force=true`, without a confirmation dialog, and without error handling. If the backend returns `409 store_referenced`, the UI can appear to do nothing.

Saved Questions are stored as `QueryRun` rows. A `QueryRun` can reference a Vector Store through `QueryRun.vector_store_id`. Query details are stored through `QueryDivisionResult` and `QuerySource` rows. `QueryRun.division_results` and `QueryDivisionResult.sources` have ORM delete cascades, but `QuerySource` also stores `query_run_id`, so implementation should be explicit enough to avoid foreign-key surprises.

## Proposed Behavior
Deleting an inactive Vector Store deletes the Vector Store and all Saved Questions that reference it.

Backend behavior:
- If the Vector Store does not exist, keep returning `404 store_not_found`.
- If the Vector Store is active, keep returning `400 store_active`.
- If the Vector Store is inactive, delete all related Saved Question data, then delete the Vector Store registry row and Chroma files.
- Remove or ignore the old `force` requirement for referenced stores because deleting referenced Saved Questions becomes the normal inactive-store delete behavior.
- Clear cached Vector Store clients after deletion as today.

Frontend behavior:
- If `store.query_count > 0`, show a browser confirmation before delete with wording that makes the Saved Question deletion explicit.
- If `store.query_count === 0`, delete without the Saved Question warning.
- On successful delete, invalidate both `vectorStores` and `conversations` queries.
- On failed delete, show the API error in the existing storage status area instead of silently failing.

## Relevant Files
- `app/api/endpoints/storage.py`
- `app/services/storage_registry.py`
- `app/db/models.py`
- `frontend/src/App.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/types/api.ts`
- `tests/test_rag_service_units.py`

## Assumptions
- Saved Questions tied to a deleted Vector Store should be deleted, not orphaned or retained with missing source hydration.
- Active Vector Stores remain protected from deletion.
- Existing `VectorStoreInfo.query_count` is sufficient for frontend confirmation copy.
- Existing `queryKeys.conversations` invalidation will refresh the History panel after deletion.
- Browser `window.confirm` is acceptable for this first version because the current UI already uses direct table actions and no modal confirmation system is established for this flow.

## Open Questions
None. User approved implementation.

## Execution Steps
- [x] Add a storage-registry helper such as `delete_vector_store_with_saved_questions(db, store)` that deletes Saved Questions referencing the store and returns the deleted Saved Question count.
- [x] Implement deletes in an FK-safe order: `QuerySource` rows for matching runs, `QueryDivisionResult` rows for matching runs, `QueryRun` rows, then the `VectorStore` row. Also explicitly delete `VectorStorePartition` rows for the store.
- [x] Update `DELETE /api/storage/vector-stores/{store_id}` to use the helper, remove the `store_referenced` blocking branch, and keep active-store protection.
- [x] Update frontend delete handling to confirm when `query_count > 0`, catch errors, update storage status text, and invalidate `queryKeys.vectorStores` plus `queryKeys.conversations`.
- [x] Add backend tests for deleting an inactive referenced Vector Store and confirming related Saved Question rows are gone.
- [x] Add backend tests that active Vector Store deletion remains blocked.
- [x] Use TypeScript frontend build for this narrow UI behavior because no frontend unit-test pattern exists for this flow.

## Validation
- `python3 -m pytest tests/test_rag_service_units.py -k "delete_vector_store or delete_store_endpoint or conversation"`: passed.
- `python3 -m pytest tests/test_rag_service_units.py tests/test_ingestion_service.py tests/test_query_models.py`: 67 passed, 1 failed on unrelated DeepSeek profile expectation (`resolve_model("quick", "map").reasoning_effort == "high"` while current code returns `None` for `deepseek-v4-flash`).
- `npm run build:frontend`: passed with existing Vite font-resolution/chunk-size warnings.
- `git diff --check`: passed.
- Manual smoke:
  - create or identify an inactive Vector Store with Saved Questions
  - click Delete
  - confirm the warning
  - verify the store disappears
  - verify those Saved Questions disappear from History
  - verify active store delete remains disabled in UI and blocked by API

## Documentation
No public setup docs are expected to change.

If implementation changes API semantics materially enough to document, add a brief note to `docs/ARCHITECTURE.md` or `CONTEXT.md` that deleting a Vector Store deletes Saved Questions backed by that store.

## Progress
- 2026-05-07: Inspected current backend and frontend delete paths. Wrote execution plan.
- 2026-05-07: Implemented backend Saved Question deletion helper and updated delete endpoint to remove referenced history for inactive Vector Stores.
- 2026-05-07: Added frontend confirmation/error handling and History invalidation.
- 2026-05-07: Added focused backend tests and ran validation.

## Decisions
- Delete referenced Saved Questions as part of inactive Vector Store deletion.
- Keep active Vector Store deletion blocked.
- Use explicit child-row deletion instead of relying solely on ORM cascades, because `QuerySource` has both `query_run_id` and `query_division_result_id`.
- Use existing `query_count` for frontend warning text.

## Discoveries
- Current frontend delete handler has no error handling, so backend `409 store_referenced` can look like no-op behavior.
- Backend already computes `query_count` per Vector Store for list responses.
- The existing `force` parameter is not surfaced in the frontend.
- Existing broader backend validation still has the unrelated DeepSeek profile test mismatch from before this plan.

## Remaining Work
- Optional manual smoke against the running app with a real inactive Vector Store that has Saved Questions.
- Unrelated DeepSeek model-strategy test mismatch remains for a separate workstream.
