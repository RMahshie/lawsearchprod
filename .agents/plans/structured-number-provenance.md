# Structured Number Provenance

## Goal
Add structured number provenance so source-backed figures and synthesized dollar totals can show hover details with source-backed input figures, readable calculation explanations, and concise rationale.

## Non-Goals
- Do not expose hidden model chain-of-thought.
- Do not replace the whole markdown answer with a structured report tree.
- Do not recompute derivations when loading saved history.
- Do not remove existing source-backed hovers for atomic numbers.
- Do not show derived hovers for unverified or partially source-backed calculations.
- Do not limit derived hovers to final synthesis only; reduce-stage division answers may also contain calculated totals.

## Current Behavior
The backend returns markdown answers, division reductions, and source chunks. The frontend scans rendered answer text for dollar figures, searches returned source snippets for matching numbers, and wraps matching figures with popovers. If an exact source match is unavailable, the frontend may fall back to nearby division marker sources.

This works for atomic figures that appear in retrieved chunks, but synthesized totals produced by the model do not exist verbatim in source chunks. Those totals cannot reliably show how the retrieved source figures add up. Saved history persists the answer, division results, and source chunk references, then rehydrates source text from Chroma by `chunk_id`.

## Proposed Behavior
The backend should own number provenance as structured response data. Answers can remain markdown, but generated figures should be tied to hidden number markers that the frontend strips before rendering.

Each visible figure should map to a `number_annotations` entry:
- `source` annotations for atomic figures backed by retrieved chunks.
- `derived` annotations for reduce-stage or final-answer synthesized totals backed by tracked source annotations and verified arithmetic.

The map stage should create source-backed number IDs and return extracted facts with inline markers such as `$10.2 billion [[num:src_dhs_1]]`. Reduce and synthesis should use structured LLM output containing both marked markdown answer text and a list of new derived annotations. For example, a reduce output can contain `$19.5 billion [[num:drv_dhs_1]]` plus a JSON object explaining that `$10.2 billion for Disaster Relief Fund + $9.3 billion for emergency preparedness = $19.5 billion in FEMA-related accounts`.

The LLM is responsible for placing derived markers and proposing the matching derived annotation objects because it writes the answer text. The backend is responsible for treating those IDs as proposals: validate marker presence, ID uniqueness, input IDs, source grounding, and deterministic arithmetic before exposing annotations. If every input is not source-backed or arithmetic validation fails, omit the derived hover and render the figure as plain text or with the existing source fallback when applicable.

Derived hovers should show the displayed total, the readable equation sentence, source-backed inputs, division badges, short source summaries, inline snippets, and a concise model-written rationale. Nested derived inputs should flatten to original chunk-backed numbers in the hover while allowing the explanation to mention a subtotal when helpful.

## Relevant Files
- `app/services/rag_service.py`
- `app/models/query.py`
- `app/db/models.py`
- `app/services/storage_registry.py`
- `frontend/src/types/api.ts`
- `frontend/src/components/QueryResults.tsx`
- `tests/test_rag_service_units.py`

## Assumptions
- V1 captures synthesized dollar totals in both division reductions and the final answer.
- Atomic/source number hovers remain available.
- The preferred persistence format is a JSON snapshot on the saved query run.
- Hidden markers are internal transport markers, not user-visible chunk IDs.
- A concise rationale is acceptable; full chain-of-thought is not.
- Arithmetic validation should use normalized numeric values with a small rounding tolerance for displayed units.
- Reduce and synthesis LLM calls can use structured output models that include marked markdown plus proposed derived annotations.

## Open Questions
None for v1. Revisit after implementation if generated answer markers conflict with markdown rendering or if the chosen database JSON type needs a compatibility fallback.

## Execution Steps
- [x] Define backend API models for number annotations, calculation inputs, source references, and annotation targets in `app/models/query.py`.
- [x] Add `number_annotations` to `QueryResponse` and mirror the types in `frontend/src/types/api.ts`.
- [x] Extend graph state in `app/services/rag_service.py` to carry source number evidence, reduce-derived annotations, synthesis-derived annotations, and final validated annotations.
- [x] Revise the map prompt/output so each mapped chunk extracts source-backed dollar figures with labels, `chunk_id`, division metadata, summaries, normalized values, and inline `[[num:src_*]]` markers in extracted facts.
- [x] Revise the reduce prompt to consume marked source facts, preserve source markers when reusing atomic figures, and return structured output with marked division answer text plus proposed derived annotations for any combined dollar figures.
- [x] Revise the synthesis prompt to consume marked division answers and available annotations, preserve existing markers where applicable, and return structured output with marked final answer text plus proposed derived annotations for any additional combined dollar figures.
- [x] Add deterministic validation for proposed derived annotations; keep only annotations whose markers appear in the target answer, whose inputs exist and flatten to source-backed numbers, and whose formula matches the displayed total within tolerance.
- [x] Track annotation targets so markers render in both `response.answer` and each `division_results[].answer`.
- [x] Merge validated source, reduce-derived, and synthesis-derived annotations into `QueryResponse.number_annotations`.
- [x] Persist `number_annotations` as a JSON snapshot on saved query runs and return it from `load_conversation`.
- [x] Replace the frontend command-F-first flow with annotation-first rendering in `QueryResults`.
- [x] Render `source` popovers from source annotations and `derived` popovers with readable equation text, formula rows, input summaries, and highlighted source snippets.
- [x] Keep the current source-snippet matching as a fallback for legacy saved conversations or responses without annotations.
- [x] Update backend and frontend tests for live responses, saved history, reduce-level derived hovers, final-answer derived hovers, verified derived totals, failed validation omission, and legacy fallback behavior.

## Validation
- `python3 -m pytest tests/test_rag_service_units.py tests/test_query_models.py`
- `npm run build:frontend`
- Manual UI check with a query that produces reduce-level and final-answer totals: atomic figures should show source hovers, synthesized totals should show readable formula/input hovers, and saved history should render the same hovers without recomputation.

## Documentation
No public README change is required for v1. Update inline schema descriptions and any API examples touched by `QueryResponse`.

## Progress
- 2026-04-26: Plan created from pipeline/history review and product decisions.
- 2026-04-26: Implemented backend annotation models, marker propagation, derived validation, saved-history JSON snapshots, annotation-first frontend rendering, and focused backend/frontend validation.
- 2026-04-26: Simplified annotation models so source annotations only store chunk references, derived annotations store equation/input ids, and source text remains in hydrated `sources`.

## Decisions
- Keep markdown answers and add structured `number_annotations` instead of replacing the answer with structured blocks.
- Use hidden answer markers to bind visible figures to backend-owned annotation objects.
- Let reduce and synthesis LLM calls place derived markers and propose matching derived annotation objects, then validate them server-side.
- Capture reduce-stage and final-answer derived dollar totals for v1.
- Persist annotations as a JSON snapshot with saved query history.
- Omit derived hovers when source backing or deterministic arithmetic validation fails.
- Flatten nested derived inputs to original source-backed numbers for hover display.
- Treat `number_annotations` as provenance metadata, not mini source documents; do not store source quotes or source summaries there.

## Discoveries
- Current figure popovers are inferred in `frontend/src/components/QueryResults.tsx` by scanning answer text and source snippets.
- Backend source records are built from retrieved/mapped chunks and include `chunk_id`, `chunk_summary`, and `chunk_snapshot`.
- Saved history stores source chunk IDs and summaries, then rehydrates source text from Chroma on load.
- `QueryResults` is shared by live and saved responses, so annotation rendering can cover both paths once history returns the saved annotation snapshot.
- Reduce is a natural point for derived number creation because it combines mapped chunk facts into coherent division-level answers.

## Remaining Work
- Manual UI check with a live query that creates reduce-level and final-answer totals.
