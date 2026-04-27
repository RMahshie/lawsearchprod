# Prompt Numeric Determinism

## Goal
Make numeric answers more deterministic by adding explicit accounting-scope policy and compact few-shot examples to reduce/synthesis prompts.

## Non-Goals
- Do not change retrieval `k`, chunk size, chunk overlap, embeddings, or Chroma data.
- Do not change API models, response schemas, persistence, frontend rendering, or derived-number validation.
- Do not implement backend-computed totals or structured inclusion/exclusion schemas in this pass.

## Current Behavior
Reduce and synthesis prompts preserve number provenance markers and validate derived annotations, but they do not define a stable accounting policy for broad questions like "how much for FEMA?" or "how much for FEMA and immigration combined." Repeated runs can choose different scopes, such as including or excluding CBP, Disaster Relief Fund, component ICE figures, or FEMA subprograms.

## Proposed Behavior
The reduce prompt should explicitly prefer scoped buckets over unsupported grand totals, with examples for FEMA, immigration, and a non-FEMA/non-immigration appropriations case. The synthesis prompt should preserve those scoped buckets and caveats instead of collapsing them into unsupported totals.

## Relevant Files
- `app/services/rag_service.py`
- `tests/test_rag_service_units.py`

## Assumptions
- Default FEMA behavior is scoped buckets, not one grand total unless explicitly requested.
- Default immigration behavior is to include relevant DHS components such as CBP, ICE, USCIS, and DHS-wide immigration-related accounts when the facts support them, while breaking the answer down by agency/component instead of hiding them inside one opaque number.
- Examples should use realistic LawSearch-style figures, including observed FEMA/immigration figures where useful.

## Open Questions
None. The user approved compact few-shot examples and requested an additional non-FEMA/non-immigration example.

## Execution Steps
- [x] Add accounting-scope policy and examples to the reduce prompt.
- [x] Add synthesis prompt rules to preserve scoped answers and caveats.
- [x] Add prompt-focused unit tests.
- [x] Run focused backend tests.

## Validation
- `python3 -m pytest tests/test_rag_service_units.py tests/test_query_models.py`

## Documentation
No public documentation changes required. The execution plan records the behavior change.

## Progress
- 2026-04-26: Plan created after inspecting current inline reduce/synthesis prompts and unit test structure.
- 2026-04-26: Added accounting policy constants, compact few-shot examples, reduce/synthesis prompt injection, and prompt-capture unit tests.
- 2026-04-26: Ran `python3 -m pytest tests/test_rag_service_units.py tests/test_query_models.py`; 32 passed.
- 2026-04-26: Revised immigration policy after user feedback: include relevant components like CBP, ICE, and USCIS by default, but present a component breakdown and label any combined subtotal.
- 2026-04-26: Revised answer shape after reviewing live output: lead with "total found" values, then use topic sections with Included and Not added separately bullets.

## Decisions
- Keep this prompt-only; do not change schemas, retrieval, chunking, UI, or arithmetic code.
- Inject examples directly in the reduce prompt so the model sees the intended accounting pattern at runtime.
- For immigration questions, prefer component breakdown plus clearly scoped subtotal over excluding CBP by default.
- For lobbying-style money questions, prefer direct "total found" working numbers with visible assumptions over making the user do the arithmetic.

## Discoveries
- Current reduce prompt already preserves markers and validates derived annotations, but lacks accounting-scope rules.
- Current synthesis prompt only says to combine comparable figures and needs explicit guidance to preserve scoped caveats.
- Prompt-capture tests can validate the runtime prompt content without changing model interfaces or API schemas.

## Remaining Work
- None for this prompt-only pass.
