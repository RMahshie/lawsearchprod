# Fix Saved-Chat Figure Popovers

## Goal
Restore blue clickable dollar-figure popovers when viewing saved conversations.

## Non-Goals
Do not change saved-history persistence, Chroma rehydration, division chips, or the relevant-excerpts accordion.

## Current Behavior
Saved conversations hydrate source chunks from Chroma and show them below the answer, but some answer dollar figures are not converted into popover triggers.

## Proposed Behavior
Saved and live query responses should use the same answer renderer. Dollar figures in the answer should become blue popover triggers when they can be tied to hydrated source snippets or to the chunks cited for the same division marker.

## Relevant Files
- `frontend/src/components/QueryResults.tsx`

## Assumptions
The saved conversation endpoint returns populated `response.sources`, because excerpts are already visible below saved answers.

## Open Questions
None.

## Execution Steps
- [x] Keep the fix scoped to frontend citation matching.
- [x] Make figure extraction and normalization reusable.
- [x] Add a cited-division fallback for saved answers whose raw source text does not contain the answer's exact formatted figure.
- [x] Run frontend lint/build validation.

## Validation
- `npm run lint:frontend`
- `npm run build:frontend`

## Documentation
No external docs needed.

## Progress
- 2026-04-26: Plan created before implementation.
- 2026-04-26: Updated `QueryResults` to use the whole response for citation matching and fall back to nearby division markers.
- 2026-04-26: Validation passed with `npm run lint:frontend` and `npm run build:frontend`.

## Decisions
Use returned `division_results.source_chunk_ids` only as a fallback after source-snippet figure matching, so exact snippet-backed popovers keep priority.

## Discoveries
`QueryResults` is shared by live and saved responses; the backend saved-history loader already hydrates `SourceDocument.content_snippet`.

## Remaining Work
Complete.
