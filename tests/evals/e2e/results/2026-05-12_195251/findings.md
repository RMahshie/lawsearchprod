# E2E Eval Findings - 2026-05-12

## Run Configuration

- **Date**: 2026-05-12
- **Questions**: 25 (25 scored)
- **Vector store**: active FY2026 store from `.env`
- **Thinking speed**: normal
- **k per division**: 16
- **Concurrency**: 3
- **Judge model**: DeepSeek via `tests/evals/e2e/judge.py`
- **Duration**: 1161.2s (~19 min)
- **Results dir**: `tests/evals/e2e/results/2026-05-12_195251/`
- **Raw data**: `raw_results.json`
- **Report**: `report.md`
- **Baseline**: `tests/evals/e2e/results/2026-05-09_190748/findings.md`

## Overall Comparison

| Metric | Baseline | Current | Delta |
|--------|----------|---------|-------|
| Avg Score | 7.1 / 10 | 8.0 / 10 | +0.9 |
| Fact Recall | 79.3% | 86.6% | +7.3 pp |
| Error Rate | 7.8% | 1.7% | -6.1 pp |
| Classify Accuracy | 88.0% | 96.0% | +8.0 pp |
| Route Accuracy | 96.0% | 100.0% | +4.0 pp |

The optimization improved the suite materially. The largest gains came from CRX classification/routing, broad-topic retrieval/prompt coverage, reconciliation parent-child handling, and the judge-facing marker cleanup.

## Scores by Answer Mode

| Mode | Baseline Avg | Current Avg | Delta | Notes |
|------|--------------|-------------|-------|-------|
| direct_account_amount | 8.2 | 7.8 | -0.4 | Regressed because `direct_5` dropped to 5 and `direct_2` dropped from 10 to 9. |
| broad_topic_total | 6.4 | 8.0 | +1.6 | Strong improvements in water, housing, and remediation, but `broad_2` and `broad_4` still miss parent accounts. |
| funding_mechanism_no_amount | 8.6 | 8.8 | +0.2 | All 5 mechanism questions now classify and route correctly. |
| reconciliation_breakdown | 8.2 | 8.6 | +0.4 | Parent-child double-counting fixed for `recon_3` and `recon_4`; `recon_1` regressed sharply. |
| general_summary | 4.2 | 6.6 | +2.4 | Better summary behavior, but still the weakest mode. |

## Per-Question Comparison

| Question | Baseline | Current | Delta | Classify | Route | Current Key Issue |
|----------|----------|---------|-------|----------|-------|-------------------|
| direct_1 | 7 | 8 | +1 | OK | OK | Still misses specific user-fee types. |
| direct_2 | 10 | 9 | -1 | OK | OK | Does not explicitly name meat, poultry, and egg inspection/enforcement. |
| direct_3 | 10 | 10 | 0 | OK | OK | Perfect. |
| direct_4 | 7 | 7 | 0 | OK | OK | Misses Geographic Programs and includes set-aside dollar detail. |
| direct_5 | 7 | 5 | -2 | OK | OK | Misses many covered VA Medical Services categories. |
| broad_1 | 6 | 10 | +4 | OK | OK | Fixed. |
| broad_2 | 4 | 5 | +1 | OK | OK | Rental assistance improved but Homeless Assistance Grants parent account now omitted. |
| broad_3 | 10 | 10 | 0 | OK | OK | Perfect. |
| broad_4 | 8 | 6 | -2 | OK | OK | Omits OJP parent and Byrne JAG nesting. |
| broad_5 | 4 | 9 | +5 | OK | OK | Cleanup/remediation coverage mostly fixed. |
| mechanism_1 | 10 | 10 | 0 | OK | OK | Fixed classification. |
| mechanism_2 | 10 | 10 | 0 | OK | OK | Fixed classification. |
| mechanism_3 | 8 | 8 | 0 | OK | OK | Still misses preserved disaster-relief designations. |
| mechanism_4 | 9 | 7 | -2 | OK | OK | Date regressed to January 30 instead of February 13; missing CISA-total caveat. |
| mechanism_5 | 6 | 9 | +3 | OK | OK | Mostly fixed; missing advance-in-appropriations condition. |
| recon_1 | 10 | 5 | -5 | OK | OK | Omits Other activities and invalidates programmatic reconciliation. |
| recon_2 | 9 | 8 | -1 | OK | OK | Still misses CECR 20%/$50M cap. |
| recon_3 | 6 | 10 | +4 | OK | OK | Fixed. |
| recon_4 | 6 | 10 | +4 | OK | OK | Fixed. |
| recon_5 | 10 | 10 | 0 | OK | OK | Perfect. |
| summary_1 | 4 | 4 | 0 | OK | OK | Still misses FDA user-fee types, obligation plan, and electronic prescribing restriction. |
| summary_2 | 6 | 4 | -2 | OK | OK | Misses several Energy-Water program categories. |
| summary_3 | 6 | 9 | +3 | OK | OK | Summary-no-ledger behavior fixed. |
| summary_4 | 0 | 10 | +10 | MISS | OK | Content fixed; classifier now chooses mechanism mode, not expected summary mode. |
| summary_5 | 5 | 6 | +1 | OK | OK | Still omits key HUD programs and includes too many dollar figures. |

## Confirmed Improvements

### CRX routing and funding-mechanism classification

The baseline had 3/5 mechanism classification misses and one total route failure for `summary_4`. Current run:

- `mechanism_1` through `mechanism_5`: all classify as `funding_mechanism_no_amount`.
- `summary_4`: routes to CRX and scores 10 instead of returning an empty incompatibility answer.
- Overall routing is now 100%.

Residual issue: `summary_4` still mismatches expected answer mode (`general_summary` expected, `funding_mechanism_no_amount` actual), but the content is correct and the judge scored it 10.

### Broad-topic coverage

The targeted vocabulary/retrieval changes helped:

- `broad_1`: 6 -> 10.
- `broad_5`: 4 -> 9.
- `broad_2`: 4 -> 5, but still poor because the answer now misses the Homeless Assistance Grants parent account and major subcomponents.

The remaining broad-topic failure pattern is parent-account structure, not pure retrieval absence. `broad_2` and `broad_4` both list some relevant child or related lines while omitting or mis-nesting the parent account (`Homeless Assistance Grants`, `OJP`, `COPS`).

### Reconciliation parent-child handling

The parent-child prompt reinforcement worked for the original double-counting failures:

- `recon_3`: 6 -> 10.
- `recon_4`: 6 -> 10.

The new weak point is `recon_1`, where the answer omitted the `Other activities` line and then claimed the programmatic lines reconcile to the FDA Salaries and Expenses total. That is a completeness failure inside the reconciliation mode, not the earlier parent-child double-counting problem.

### Summary no-ledger behavior

`summary_3` improved from 6 to 9 and no longer triggers the detailed-dollar-breakdown error. This validates the summary prompt changes for at least one multi-division summary.

## Remaining Failure Clusters

### 1. General summaries still miss broad provision coverage

`general_summary` improved from 4.2 to 6.6 average but remains the weakest mode. Current low scores:

- `summary_1` (4): misses FDA user-fee types, the 30-day obligation plan, and the electronic prescribing-information restriction.
- `summary_2` (4): misses several Energy-Water category examples: DOE defense cleanup, nuclear/atomic energy defense, tribal/fossil/renewable/grid/power administration categories, hydropower, Reclamation, regulatory activities, and administration/OIG.
- `summary_5` (6): misses major HUD-side local-government areas and is still too ledger-like.

Likely cause: summary questions need breadth-oriented retrieval and map extraction, while current retrieval still clusters around central appropriation chunks. Increasing k helped some cases, but not enough for division-wide "what does this division do" questions.

### 2. Parent account preservation remains inconsistent in broad answers

Current examples:

- `broad_2`: child homelessness items appear, but the answer omits the Homeless Assistance Grants parent total and two required subcomponents.
- `broad_4`: answer omits the OJP parent account and total, does not nest Byrne JAG under OJP, and misplaces several COPS subprograms outside COPS.

Suggested next fix: strengthen broad-topic reduce/synthesis to require parent-account preservation when child/subprogram facts are present. This is similar to reconciliation parent-child logic but for broad-topic grouping.

### 3. Direct account answers can be too generic on covered activities

`direct_5` dropped from 7 to 5 because the answer gave the VA Medical Services amount but omitted many required service categories. `direct_1` and `direct_2` also missed specific required category lists.

Suggested next fix: for `direct_account_amount`, preserve enumerated statutory activity lists when they are in the retrieved/mapped facts, while still avoiding full breakdown tables unless asked.

### 4. CRX mechanism answers need a small date/condition guardrail

`mechanism_4` regressed from 9 to 7 because it used January 30, 2026 instead of February 13, 2026 and omitted the caveat that a CISA dollar total would require a separate line-item appropriation or referenced baseline. `mechanism_5` still misses the "payments and reimbursements only to the extent and in amounts provided in advance" condition.

Suggested next fix: add CRX-specific prompt language that prioritizes extension dates and advance-appropriations payment conditions.

## Infrastructure Notes

- The run produced repeated LangSmith 429 trace-upload warnings because the monthly unique traces limit was exceeded. These did not stop the eval and did not affect local report generation.
- A concurrency retrieval race was found during subset runs before this full run: parallel eval questions could query a Chroma store after another thread changed the active embedder/store pairing. `VectorStoreService` now serializes store resolution and Chroma query access with a reentrant lock.
- The invalid sandbox/network attempt at `tests/evals/e2e/results/2026-05-12_175954/` should not be used for scoring.

## Recommended Next Pass

1. Fix broad-topic parent preservation for OJP/COPS and Homeless Assistance Grants.
2. Add summary-mode retrieval or prompt support for division-wide provision breadth, especially FDA peripheral provisions and Energy-Water category coverage.
3. Add direct-mode preservation of enumerated covered activities for service accounts like VA Medical Services and FDA/FSIS.
4. Add CRX date and advance-appropriations condition guardrails.
5. Re-run a targeted subset first: `broad_2,broad_4,direct_5,recon_1,summary_1,summary_2,summary_5,mechanism_4,mechanism_5`.
