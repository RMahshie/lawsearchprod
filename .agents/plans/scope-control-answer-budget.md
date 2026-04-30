# Scope Control and Answer Budget

## Goal
Improve RAG answer quality for broad appropriations questions by keeping retrieval/generation within the user's actual scope and preventing final answers from becoming dense reconciliation memos. The system should still preserve useful detail for direct responsive funding, but adjacent or weakly responsive divisions should be clearly identified and kept short.

## Non-Goals
- Do not change ingestion, vector-store layout, or chunking.
- Do not remove source citations, number markers, derived annotation validation, or source hover behavior.
- Do not hard-code topic-specific behavior for rural water/wastewater, THUD, SFOPS, or any other named example.
- Do not hide direct responsive accounts merely to make answers shorter.
- Do not expose new relevance metadata in the public `QueryResponse` unless explicitly approved later.

## Current Behavior
The route-integrated answer-mode classifier now selects an answer mode and safety flags, and map/reduce/synthesis assemble modular prompts from `app/services/rag_prompting.py`.

For the question "What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it?", the system selected and synthesized multiple divisions. The answer was more financially correct than before because it avoided a single bad mixed-type total, but it was too dense:
- It included direct responsive material from USDA/RUS and EPA.
- It also included weak or adjacent water-related material from THUD and SFOPS.
- It preserved too many suballocations, caveats, and division details.
- It repeated caveats in division sections and again at the end.
- Synthesis mostly appended division-level answers rather than compressing them.

## Proposed Behavior
Add explicit responsiveness tiers and answer-budget rules across map, reduce, and synthesis.

Responsiveness tiers:
- `direct`: directly answers the user's topic and scope.
- `adjacent`: related terms or funding, but not clearly within the user's requested scope.
- `not_responsive`: retrieved material that should not be used to answer the question.

Map should support mixed evidence within one chunk. A chunk can produce multiple facts, and each fact should carry its own responsiveness tier. This likely requires changing map structured output from a plain markdown string plus `source_numbers` into a list of fact objects or an equivalent structured shape. Each fact should include:
- fact text
- responsiveness tier
- short reason or scope note
- source/citation marker context
- source numbers, when applicable

Relevance-tier debug storage should exist at three levels:
- per fact: the actual `direct`, `adjacent`, or `not_responsive` tier
- per chunk: tier counts only
- per division: tier counts plus short direct/adjacent summary

Reduce should build real answer content from `direct` facts. `adjacent` facts should be used only for short "not included / adjacent" notes unless they are necessary to clarify scope. `not_responsive` facts should not appear in final answer content.

Source-number annotations should be created for adjacent facts only when those adjacent facts are actually surfaced in the answer. Adjacent facts that are collapsed away should not create final hoverable numbers.

Weak or adjacent divisions that the router selected should be included in the final answer as short not-included lines, not full sections. Example shape:
- `THUD: no direct responsive funding found in retrieved facts; related community-development material was not specific enough to count.`

Broad mixed-topic answers should use a medium-plus answer budget:
- Target 8-12 substantive bullets for the main answer, plus a short intro paragraph if needed.
- The answer can exceed 12 bullets only when there are more than 12 direct responsive accounts or buckets that materially answer the question.
- Keep all direct responsive accounts/buckets when they are actually direct.
- Suballocations are valuable for this product and should be kept when they are direct and useful to the user, but they should be grouped compactly and not repeated as caveats.

Synthesis should mostly combine already-short division results. Reduce should produce shorter, scoped division outputs so synthesis does not need to aggressively rewrite long text. Synthesis should still enforce final budget rules:
- short top-level answer
- group broad answers primarily by controlling agency/account, with division labels secondary
- include short not-included division notes for routed divisions without direct evidence
- avoid duplicating caveats already stated next to the relevant bucket

Answer-budget enforcement should use both prompt rules and debug logging. The system should not fail a query for exceeding budget, but should log word/bullet counts when generated answers exceed the target.

## Relevant Files
- `app/services/rag_service.py`
- `app/services/rag_prompting.py`
- `app/models/query.py` if structured relevance metadata needs a model type
- `app/db/models.py`, `app/db/session.py`, and `app/services/storage_registry.py` if relevance metadata is persisted for debugging
- `tests/test_rag_service_units.py`
- `.agents/skills/lawsearch-rag-debugging/SKILL.md`
- `.agents/plans/scope-control-answer-budget.md`

## Assumptions
- This change is broader than prompt text only; structured map output changes are allowed.
- Relevance tiers should be stored for logging/debugging.
- Relevance tiers should remain internal and not be returned in `QueryResponse`.
- The final answer should mention selected divisions with no direct evidence using short "no direct info found" phrasing.
- "Rural water or wastewater infrastructure" is an example of the failure mode, not a topic-specific rule to hard-code.
- Users often want enough detail to inspect accounts and then open the source documents themselves, so direct responsive detail should not be over-compressed.

## Open Questions
- None currently. Reopen this section if implementation discovers a plan-level issue.

## Execution Steps
- [x] Inspect current map structured output, source-number marker insertion, reduce inputs, and final synthesis flow.
- [x] Define internal relevance-tier models or typed dicts for mapped facts.
- [x] Update map structured output so each extracted fact can carry `direct`, `adjacent`, or `not_responsive`.
- [x] Preserve source-number annotation behavior for direct facts and define behavior for adjacent facts after resolving the open question.
- [x] Update reduce prompt assembly so direct facts form the answer and adjacent facts collapse into short not-included notes.
- [x] Update synthesis prompt assembly so broad answers use a medium-plus budget and combine scoped division results instead of appending dense sections.
- [x] Add debug logging for relevance-tier counts by route/division/stage.
- [x] Persist relevance-tier debug metadata at per-fact, per-chunk-count, and per-division-summary levels.
- [x] Add answer-budget debug logging for generated answers that exceed target word/bullet counts.
- [x] Add tests for fact-level relevance tiers, mixed direct/adjacent facts in one chunk, non-responsive routed divisions collapsing to one line, and prompt budget rules.
- [x] Run focused backend validation and update this plan with decisions, discoveries, validation, and remaining work.

## Validation
- `python3 -m pytest tests/test_rag_service_units.py tests/test_ingestion_service.py tests/test_query_models.py`
- Prompt-capture tests should verify:
  - map asks for fact-level responsiveness tiers
  - reduce excludes `not_responsive` facts
  - reduce collapses adjacent-only divisions
  - synthesis has 8-12 bullet target behavior for broad answers
  - synthesis does not duplicate caveats across division sections and final caveats
- Optional live-query checks with a populated FY2026 vector store:
  - rural water/wastewater infrastructure
  - a direct account question that should preserve concise output
  - a broad mixed financial-type question with adjacent retrieved facts

## Documentation
Update `.agents/skills/lawsearch-rag-debugging/SKILL.md` if new debug logs are added for relevance-tier counts or answer-budget warnings.

## Progress
- 2026-04-30: Plan created from observed rural water/wastewater answer behavior and user answers. No implementation changes made.
- 2026-04-30: User confirmed remaining decisions: store relevance tiers at fact/chunk/division levels, annotate adjacent numbers only when surfaced, group broad answers by controlling agency/account with division secondary, include short adjacent reasons in no-direct-info lines, use prompt budget plus debug logging, and show all truly direct suballocations compactly.
- 2026-04-30: Implemented fact-level responsiveness tiers, tiered map rendering, direct-only source annotations, reduce/synthesis scope and budget prompt rules, relevance debug persistence, and answer-budget logging.
- 2026-04-30: Validation passed with `python3 -m pytest tests/test_rag_service_units.py tests/test_ingestion_service.py tests/test_query_models.py`.

## Decisions
- Use responsiveness tiers: `direct`, `adjacent`, `not_responsive`.
- Weak/adjacent routed divisions should be included as short not-included lines, not full sections.
- Map should be able to classify mixed evidence within one chunk.
- The answer budget for broad mixed-topic answers should be medium-plus: roughly 8-12 substantive bullets plus a short paragraph, unless more direct responsive accounts truly require more.
- Suballocations are useful product detail and should be preserved when direct, but grouped compactly and not repeated in caveats.
- Reduce should produce shorter scoped division outputs so synthesis can mostly combine results.
- Relevance metadata should be stored/logged for debugging but not exposed in the public response.
- Avoid topic-specific hard-coded rules.
- Relevance-tier debug storage should include per-fact tiers, per-chunk counts, and per-division counts/summaries.
- Adjacent source-number annotations should only be created when the adjacent fact appears in the answer.
- Broad final answers should group primarily by controlling agency/account, with division labels secondary.
- No-direct-info lines should include a short adjacent reason when available.
- Answer budget should be enforced by prompt guidance and debug logging, not hard failure.
- If many suballocations are truly direct, show them all, but group them compactly under the parent account.

## Discoveries
- The existing source-number marker insertion could be preserved by rendering direct facts separately before adding markers. Adjacent facts are still available for scope notes, but their numbers are not marked unless they become direct surfaced evidence.

## Remaining Work
- Optional live-query checks with a populated FY2026 vector store.
