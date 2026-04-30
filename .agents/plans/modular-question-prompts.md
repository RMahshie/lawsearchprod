# Modular Question Prompts

## Goal
Refactor the RAG generation prompts so invariant rules stay small and always on, while question-specific instructions are selected by an explicit answer-mode classification. The change should reduce prompt bloat, keep source/provenance safety intact, and make direct account questions, broad totals, mixed financial-type questions, funding-mechanism answers, and reconciliation-style answers use different prompt modules.

## Non-Goals
- Do not change retrieval, ingestion, vector-store layout, chunking, or frontend rendering.
- Do not add new response fields or persist new metadata unless implementation discovers that prompt selection cannot be debugged without it.
- Do not replace the current `map -> reduce -> synthesize` graph.
- Do not remove existing number provenance markers, derived annotation validation, or source hover behavior.
- Do not make classification a brittle hard gate that can silently drop accounting safety rules.

## Current Behavior
The current prompts in `app/services/rag_service.py` use large shared policy blocks:
- `ACCOUNTING_SCOPE_POLICY` contains concise-answer, funding-mechanism, double-counting, and mixed-financial-type rules.
- `ACCOUNTING_FEW_SHOT_EXAMPLES` includes examples for FEMA, immigration, Army Corps, funding-mechanism-no-amount, FDA direct account answers, and rural water/wastewater mixed financial types.
- `_map_chunk` always receives the same extraction rules, including funding-mechanism and financial-type preservation rules.
- `_reduce_division` always receives the full accounting policy and all examples, even when the question only needs a direct account answer.
- `_synthesize_final` always receives the broad synthesis accounting policy.

This keeps behavior centralized, but it makes every generation stage carry rules and examples that may not apply to the current question.

## Proposed Behavior
Add a lightweight answer-mode classification step and modular prompt assembly.

The system should classify the user question as soon as the query enters the RAG flow by extending the existing nano routing structured-output call. Do not add a separate classifier model call unless implementation proves route integration is not viable and the plan is revised first. The classifier should pick the best answer mode from:
- `direct_account_amount`: a specific account/program amount or allowed-use question.
- `broad_topic_total`: a topic total across accounts, agencies, or divisions where comparable additive buckets may exist.
- `funding_mechanism_no_amount`: questions where the likely answer may be continuing appropriations, rate-for-operations, extension, apportionment, or referenced prior-law language rather than a new dollar figure.
- `reconciliation_breakdown`: questions asking for breakdowns, what was included/excluded, double-counting, totals across named topics, or accounting reconciliation.
- `general_summary`: non-numeric or lightly numeric explanatory questions.

The classifier should also return safety flags. The first required flag is `mixed_financial_types`, used for questions likely to retrieve grants, loan authority, subsidy costs, user fees, transfers, rescissions, caps, limitations, or other non-comparable financial types. This is a flag, not a standalone mode, because a question can be both a broad topic total and mixed financial type.

The classifier should be LLM-based with `gpt-5.4-nano`, not deterministic rules. Invalid classifier structured output should fail loudly rather than silently falling back, because this should be a simple classification task and bad classifier state should not be hidden. For valid but ambiguous classification, default to `broad_topic_total`; this should behave like a broad numeric summary/total mode, leading with a total only when comparable additive buckets support it and otherwise using grouped summary buckets.

Prompt assembly should use:
- small invariant core instructions for all stages
- always-on safety/accounting constraints
- mode-specific map instructions
- mode-specific reduce instructions
- mode-specific synthesis instructions
- mode-specific examples only when useful

The selected mode should be carried through the graph state and used consistently by map, reduce, and synthesize. Synthesis should not independently pick a new mode.

The selected mode should remain internal to the API response, but it should be persisted with saved conversations and logged under `DEBUG=true` for debugging.

Persisted classifier debug state should include `answer_mode`, `answer_mode_flags`, and a short classifier reason/debug string. It should not be exposed in `QueryResponse`.

Prompt modules should move out of `rag_service.py` into a dedicated module, likely `app/services/rag_prompting.py`.

Always-on invariant instructions should include:
- preserve source, citation, and number markers
- do not invent facts, dollar figures, or totals
- use only retrieved facts
- only sum comparable additive amounts
- preserve caveats for transfers, rescissions, caps, fees, set-asides, suballocations, limitations, and non-comparable accounts
- do not substitute unrelated dollar figures when the requested topic lacks a dollar amount
- distinguish funding-mechanism evidence from dollar-figure evidence

Broad topic total mode should lead with a "total found" only when the user asks "how much" and retrieved facts contain top-level comparable additive buckets. If the facts are mixed or hierarchy is unclear, lead with grouped buckets instead.

Reconciliation/breakdown mode should trigger for wording like "breakdown", "show math", "included", "excluded", "not added", "double count", "reconcile", "combined", "total across", "why", and "compare". It should also trigger when the user asks about multiple named topics and a combined total.

Funding-mechanism mode should be selected from the original question when obvious, but map/reduce should still be able to report mechanism evidence when retrieval finds relevant mechanism text and no topic-specific dollar figure.

Synthesis should become a lighter combiner once answer mode is selected: write a short top-level summary, preserve or append the division-level results, and avoid doing new accounting unless combining comparable division totals.

Expected example placement:
- Map keeps a small general extraction example.
- Reduce gets the scenario-specific examples for the selected mode.
- Synthesis gets one simple combining example, if needed.

## Relevant Files
- `app/services/rag_service.py`
- `tests/test_rag_service_units.py`
- Optional new helper module if prompt assembly grows too large for `rag_service.py`, for example `app/services/rag_prompting.py`
- `.agents/plans/modular-question-prompts.md`

## Assumptions
- The first implementation should keep classification out of the public `QueryResponse`, but it may need model/database changes to persist answer mode for saved conversations.
- Classification should use `gpt-5.4-nano` structured output.
- The classifier should select the best mode from the defined mode set.
- The classifier should return `mixed_financial_types` as a safety flag.
- Existing source marker and derived annotation rules remain invariant and should not be mode-specific.
- Existing tests that capture prompt text should be rewritten around prompt modules instead of asserting one monolithic prompt.

## Open Questions
- None currently. Reopen this section if implementation discovers a plan-level issue.

## Execution Steps
- [x] Inspect the current route structured-output flow and extend it to carry answer-mode classification.
- [x] Define an `AnswerMode` enum or equivalent constants.
- [x] Define an `AnswerModeFlags` shape including `mixed_financial_types`.
- [x] Implement a `gpt-5.4-nano` structured-output classifier. Invalid structured output fails loudly.
- [x] Implement `broad_topic_total` as the explicit default mode for valid-but-ambiguous classifier output.
- [x] Split prompt text into modules: invariant core, provenance/marker rules, accounting safety rules, and mode-specific stage modules.
- [x] Update `_map_chunk`, `_reduce_division`, and `_synthesize_final` to assemble prompts from the selected modules.
- [x] Ensure synthesis receives and uses the selected answer mode from query state.
- [x] Add `DEBUG=true` logging for selected answer mode.
- [x] Persist `answer_mode`, `answer_mode_flags`, and classifier debug reason with saved conversations for debugging.
- [x] Keep the current behavior for direct account questions: concise answer, no unnecessary "Not added separately" section, and no nearby provisions.
- [x] Keep the current behavior for mixed financial-type questions: group by type, sum only comparable additive amounts, and label any mixed arithmetic as a mixed identified total.
- [x] Add prompt-capture tests for each answer mode and verify irrelevant examples are excluded from simple modes.
- [x] Add classifier tests for representative questions, including FDA Salaries and Expenses, FEMA amount, rural water/wastewater infrastructure, continuing appropriations/FEMA mechanism, and explicit breakdown/reconciliation prompts.
- [x] Run focused backend tests and update this plan with decisions, discoveries, validation, and remaining work.

## Validation
- `python3 -m pytest tests/test_rag_service_units.py tests/test_ingestion_service.py tests/test_query_models.py`
- Manual prompt inspection through prompt-capture tests for:
  - direct account amount
  - broad topic total
  - mixed financial types
  - funding mechanism without explicit amount
  - reconciliation/breakdown
- Optional live-query checks after implementation with a populated FY2026 vector store:
  - FDA Salaries and Expenses amount and major allowed uses
  - rural water/wastewater infrastructure funding
  - FEMA/DHS continuing appropriations mechanism question

## Documentation
No user-facing documentation is expected. Because answer-mode logging should be added, document the debug log line in `.agents/skills/lawsearch-rag-debugging/SKILL.md`.

## Progress
- 2026-04-29: Plan created after discussion. No implementation changes made.
- 2026-04-29: User clarified that classification should use `gpt-5.4-nano`, should happen at query start or existing route step, should fail loudly on invalid structured output, should be internal/logged/persisted, prompt modules should move to their own file, and implementation must stop for approval after plan update.
- 2026-04-29: User confirmed `mixed_financial_types` should be a safety flag, broad topic totals should lead with totals only when comparable top-level buckets exist, funding-mechanism behavior should remain available after retrieval, synthesis should become a lighter combiner, and classifier debug persistence should include mode plus flags/reason.
- 2026-04-29: User chose `broad_topic_total` as the valid-ambiguous default and confirmed answer-mode classification should be integrated into the existing nano route structured-output call.
- 2026-04-29: Implemented route-integrated answer-mode classification, modular prompt assembly, graph-state propagation, debug logging, saved-conversation persistence, and prompt-capture tests.
- 2026-04-29: Validation passed with `python3 -m pytest tests/test_rag_service_units.py tests/test_ingestion_service.py tests/test_query_models.py`.

## Decisions
- Prompt selection should be modular rather than separate fully duplicated prompts.
- Source marker preservation, derived annotation rules, no-invented-totals rules, and comparable/additive aggregation safety should remain invariant.
- Mode-specific examples should be included only where they are likely to help the current question.
- Classification should be LLM-based with `gpt-5.4-nano`.
- Invalid classifier structured output should fail loudly.
- The selected answer mode should be logged under `DEBUG=true`.
- The selected answer mode should be persisted for saved-conversation debugging.
- The selected answer mode should remain internal and not be added to `QueryResponse`.
- Prompt modules should move to a dedicated module such as `app/services/rag_prompting.py`.
- The selected mode should be decided before retrieval and carried through map, reduce, and synthesize.
- `mixed_financial_types` should be a safety flag, not a standalone answer mode.
- Valid-but-ambiguous classifier output should default to `broad_topic_total`, behaving as a broad numeric summary/total mode.
- Classification should be integrated into the existing route nano structured-output call.
- Broad topic totals should lead with a total found only when the user asks for an amount and the facts contain comparable top-level additive buckets.
- Reconciliation mode should trigger for breakdown, show math, included/excluded/not added, double count, reconcile, combined, total across, why, compare, and multi-topic combined-total questions.
- Funding-mechanism behavior should be selected upfront when obvious, but still remain available in map/reduce when retrieval finds mechanism evidence and no topic-specific dollar figure.
- Synthesis should be a lighter combiner: short top-level summary plus preserved division results, with new accounting only for comparable division totals.
- Persisted classifier debug state should include `answer_mode`, `answer_mode_flags`, and a short reason/debug string.

## Discoveries
- Current prompt-capture tests already assert the monolithic accounting policy and examples. They will need to move toward module-selection assertions.
- Current synthesis prompt only runs for multiple division answers; single-division answers depend on reduce output, so reduce-mode behavior is the highest-leverage place to start.
- `divisions_filter` previously bypassed the route node before the classifier existed. The implementation now still uses the route node for classification, but filtered divisions remain authoritative for division selection.
- Existing incompatible-question final answers could be overwritten by the no-division synthesis path. The implementation preserves an existing final answer when synthesis has no division answers.

## Remaining Work
- Optional live-query checks with a populated FY2026 vector store.
