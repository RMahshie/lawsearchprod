# E2E Eval Findings — 2026-05-09

## Run Configuration

- **Date**: 2026-05-09
- **Questions**: 25 (5 per answer mode)
- **Vector store**: voyage-law-2 (`609b2b98-104e-4286-b410-a34337ba0ed5`)
- **Thinking speed**: normal
- **k per division**: 12
- **Concurrency**: 3
- **Judge model**: DeepSeek v4 pro (reasoning_effort=high)
- **Pipeline**: classify → route → rewrite → retrieve → map → reduce → synthesize (LangGraph, `RAGService._graph.invoke()`)
- **Duration**: 1192.5s (~20 min)
- **Results dir**: `tests/evals/e2e/results/2026-05-09_190748/`
- **Raw data**: `raw_results.json` (full pipeline state + judge output per question)
- **Report**: `report.md` (4-level markdown report)
- **Gold references**: `tests/evals/e2e/gold_references.py` (25 GoldReference dataclasses)

## Overall Scores

| Metric | Value |
|--------|-------|
| Avg Score | 7.1 / 10 |
| Fact Recall | 79.3% |
| Error Rate | 7.8% |
| Classify Accuracy | 88.0% (22/25) |
| Route Accuracy | 96.0% (24/25) |

## Scores by Answer Mode

| Mode | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-----------|-------------|------------|----------|-------|
| direct_account_amount | 8.2 | 85.7% | 9.5% | 100% | 100% |
| broad_topic_total | 6.4 | 64.7% | 7.7% | 100% | 100% |
| funding_mechanism_no_amount | 8.6 | 84.0% | 0.0% | 40% | 100% |
| reconciliation_breakdown | 8.2 | 94.7% | 7.4% | 100% | 100% |
| general_summary | 4.2 | 42.3% | 14.3% | 100% | 80% |

## Per-Question Scores

| Question | Score | Classify | Route | Key Issue |
|----------|-------|----------|-------|-----------|
| direct_1 | 7 | OK | OK | Judge flagged `[[num:...]]` markers as internal language; missed user-fee detail |
| direct_2 | 10 | OK | OK | Perfect |
| direct_3 | 10 | OK | OK | Perfect |
| direct_4 | 7 | OK | OK | Missed Geographic Programs $690,202,000 set-aside |
| direct_5 | 7 | OK | OK | Missed priority groups 1-6; annotation markers flagged |
| broad_1 | 6 | OK | OK | Missed EPA Clean Water SRF $1.6B and Drinking Water SRF $1.1B |
| broad_2 | 4 | OK | OK | Missed tenant-based ($34.4B) and project-based ($18.1B) rental assistance entirely |
| broad_3 | 10 | OK | OK | Perfect |
| broad_4 | 8 | OK | OK | Missed Tribal law enforcement $32M and Daniel Anderl grant $7.5M |
| broad_5 | 4 | OK | OK | Missed brownfields grants $98M, LUST $88.9M, Superfund activities $77.1M |
| mechanism_1 | 10 | MISS | OK | Classified as broad_topic_total but answer was still correct |
| mechanism_2 | 10 | MISS | OK | Classified as general_summary but answer was still correct |
| mechanism_3 | 8 | OK | OK | Missed February 13, 2026 extension date |
| mechanism_4 | 9 | OK | OK | Missed detail about what would be needed for a dollar total |
| mechanism_5 | 6 | MISS | OK | Classified as general_summary; missed specific payment types and advance-in-appropriations rule |
| recon_1 | 10 | OK | OK | Perfect |
| recon_2 | 9 | OK | OK | Missed CECR prior-year 20%/$50M limitation |
| recon_3 | 6 | OK | OK | Double-counting: suballocations in Included alongside parents |
| recon_4 | 6 | OK | OK | Missing two grant programs; SRF suballocations in Included alongside parents |
| recon_5 | 10 | OK | OK | Perfect |
| summary_1 | 4 | OK | OK | Missed obligation plan, electronic prescribing restriction, user-fee types |
| summary_2 | 6 | OK | OK | Missed regulatory programs, formerly utilized sites cleanup, flood control |
| summary_3 | 6 | OK | OK | Too detailed — included many dollar figures when summary was requested |
| summary_4 | 0 | OK | MISS | Route returned [] — no divisions selected, answer was empty refusal |
| summary_5 | 5 | OK | OK | Missed transportation programs, HUD programs, distinct-accounts concept |

---

## Finding 1: Classify stage fails on `funding_mechanism_no_amount` (3/5 misclassified)

### What happened

Three mechanism questions were misclassified:
- `mechanism_1` → `broad_topic_total` (reason: "Asks about overall DHS funding handling and full-year amount")
- `mechanism_2` → `general_summary` (reason: "Asks about the purpose and funding mechanism of a specific appropriations act")
- `mechanism_5` → `general_summary` (reason: "Explains the effect of a continuing resolution without full-year appropriation")

### Why it matters

The wrong answer_mode changes the map/reduce/synthesis prompts. `broad_topic_total` prompts try to group funding lanes and compute totals. `funding_mechanism_no_amount` prompts explicitly say "do not invent or infer a dollar figure" and focus on mechanism language. Despite misclassification, scores were still high (10, 10, 6) because CRX chunks contain mechanism language that surfaces correctly — but `mechanism_5` scored only 6 because the general_summary mode prompts didn't push the model to extract the specific payment-type details that the mechanism prompts would have.

### Root cause

The classify stage prompt (in `app/services/rag/stages/classify.py`) likely lacks sufficient examples of mechanism questions. The pattern "how is X funded," "what mechanism," "is there an explicit amount," or "what happens under the CR" should classify as `funding_mechanism_no_amount`, but the classifier sees DHS/FEMA keywords and defaults to totals or summaries.

### Relevant files

- `app/services/rag/stages/classify.py` — classify prompt and answer mode selection logic
- `app/services/rag_prompting.py` lines 7-12 — `AnswerMode` type definition

### Suggested fix

Add explicit mechanism-question examples to the classify prompt. The distinguishing pattern is: the question asks about *how* funding works or *whether* an explicit amount exists, rather than *how much* funding is available. Examples:
- "How is DHS funding handled?" → `funding_mechanism_no_amount`
- "What funding mechanism does the CR use?" → `funding_mechanism_no_amount`
- "Does the text provide a specific dollar amount for X, or only a CR mechanism?" → `funding_mechanism_no_amount`
- "What happens to agencies under the CR without full-year appropriations?" → `funding_mechanism_no_amount`

---

## Finding 2: Route stage returns empty divisions for abstract questions (summary_4 scored 0/10)

### What happened

`summary_4` asks: "What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?" The router returned zero divisions. With no divisions, the pipeline produced no chunks, no map/reduce, and the final answer was: "This question is incompatible with the FY2026 appropriations text available in LawSearch."

### Why it matters

This is a total pipeline failure — 0/10 score. Any abstract or conceptual question that doesn't name a specific agency, program, or dollar figure risks the same fate.

### Root cause

The route stage selects divisions by matching question keywords against division routing aliases (`FY2026_ROUTING_ALIASES` in `app/core/config.py`). "Continuing appropriations" as a concept doesn't strongly match CRX's routing aliases when there's no concrete entity like "FEMA" or "DHS" in the question. The router has no fallback for zero-selection.

### Relevant files

- `app/services/rag/stages/route.py` — route division selection logic
- `app/core/config.py` — `FY2026_ROUTING_ALIASES` dict mapping division names to keyword strings

### Suggested fix (two options, not mutually exclusive)

**Option A**: Add conceptual trigger terms to CRX's routing aliases: "continuing resolution", "continuing appropriations", "regular vs continuing", "CR mechanism", "rate for operations", "full-year vs continuing".

**Option B**: Add a classify→route linkage so that when `answer_mode` is `funding_mechanism_no_amount`, CRX is always included in selected divisions (since mechanism questions are definitionally about CR-covered entities). This could also be a fallback: if the router selects zero divisions and the answer_mode suggests a specific division, inject it.

---

## Finding 3: Retrieval/map coverage gap for broad_2 — missed $52.5B in rental assistance (4/10)

### What happened

`broad_2` asks about affordable housing, rental assistance, and homelessness services in THUD. The pipeline retrieved 12 chunks and mapped 12, but the final answer only covered Homeless Assistance Grants ($4.4B) and Section 811 ($287M). It completely missed:
- Tenant-based rental assistance: $34,438,557,000
- Project-based rental assistance: $18,143,000,000
- Public Housing Fund: $8,319,393,000
- Youth homelessness: $107,000,000

The final answer's division-level summary said: "the direct funding shown here is HUD Homeless Assistance Grants and Section 811 Project Rental Assistance."

### Why it matters

This is the worst content gap in the eval. The two largest HUD programs ($34.4B + $18.1B = $52.5B) were entirely absent. This is either a retrieval failure (those chunks weren't in the top 12) or a mapping failure (the map stage classified them as `not_responsive`).

### Root cause (needs diagnosis)

**Hypothesis A (retrieval)**: The rewrite stage produced a query too narrowly focused on "homelessness" or "affordable housing" and didn't surface the rental assistance sections of the THUD division. With k=12 for one division, coverage is limited.

**Hypothesis B (mapping)**: The chunks were retrieved but the map stage for `broad_topic_total` classified tenant-based/project-based rental assistance as `not_responsive` because the question said "affordable housing" and the chunks say "tenant-based rental assistance" — a vocabulary mismatch.

### Diagnostic step

Re-run `broad_2` with debug logging enabled to see: (1) what rewrite query was produced, (2) what 12 chunks were retrieved, (3) what tier the map stage assigned to each chunk. This will disambiguate retrieval vs mapping failure.

```bash
# To diagnose, add DEBUG=true to .env and run:
.venv/bin/python3 -m tests.evals.e2e.run --questions broad_2 --reference
```

Then inspect the retrieved chunk content and map-stage tier assignments in the logs.

### Suggested fixes (depending on diagnosis)

**If retrieval gap**: Increase k to 16-20 for broad_topic_total questions (they tend to span more of a division). Or improve the rewrite prompt to expand the query scope — "affordable housing" should rewrite to include "rental assistance, public housing, homelessness, Section 8, vouchers."

**If mapping gap**: Adjust the `broad_topic_total` map prompt to be more inclusive — rental assistance is a direct funding lane for "affordable housing." The current prompt says: "Direct includes top-level funding lanes for the topic: appropriated grants, direct loan authority..." — rental assistance should be explicitly recognized as a direct funding lane when the question asks about housing/affordability.

---

## Finding 4: Reconciliation double-counting (recon_3 scored 6/10, recon_4 scored 6/10)

### What happened

**recon_3** (USDA Rural Water and Waste): The reduce stage placed suballocations in the Included section alongside their parent totals:
- `$3,876,000` appeared in Included alongside its parent `$51,476,000`
- `$110,488,564` (CPF/CDS) appeared in Included alongside its parent `$250,488,564`
- `$1,000,000` (section 306E subgrants) appeared in Included alongside its parent `$5,000,000`

**recon_4** (EPA STAG): SRF capitalization grant parent totals and their project-specific suballocations both appeared in the Included section.

### Why it matters

Double-counting is the most dangerous error in appropriations analysis. Parent + child in the same "Included" section implies they're additive, which is wrong — the child is already within the parent.

### Root cause

The reduce prompt for `reconciliation_breakdown` (in `app/services/rag_prompting.py` lines 169-227) explicitly instructs: "If a broader parent account and one of its components both appear, include the parent account and explain that the component was not added separately." But the model is not complying consistently. The map stage extracts both parent and child as `direct` facts, and the reduce stage places both in Included without checking the "of which" / "within" relationship.

### Relevant files

- `app/services/rag_prompting.py` lines 169-227 — `REDUCE_MODE_PROMPTS["reconciliation_breakdown"]`
- `app/services/rag/stages/reduce.py` — reduce stage invocation

### Suggested fix

**Prompt reinforcement**: Add a pre-emission validation instruction to the reconciliation reduce prompt: "Before finalizing the Included section, scan every amount for 'within', 'of which', 'not to exceed', or 'of the total'. If an amount is described as a subset of another Included amount, move it to Not Added Separately with a note explaining the parent-child relationship."

**Post-reduce validation (harder but more reliable)**: Add a programmatic check after the reduce stage that parses the Included section for amounts that appear as subsets of other Included amounts, based on the map-stage extracted relationship language. This would be a new validation node in the graph.

---

## Finding 5: General summary mode over-produces detail (avg 4.2/10)

### What happened

Multiple summary questions produced overly detailed answers:
- `summary_3` (water infrastructure summary): 3,074 chars with many specific dollar figures, despite the question saying "without doing a detailed dollar breakdown." The judge triggered the error "Should not provide a detailed dollar-by-dollar breakdown."
- `summary_1` (FDA summary): Missed key provisions (obligation plan, electronic prescribing restriction) while including dollar amounts that weren't needed.
- `summary_5` (THUD for local governments): Missed high-level categorization of transportation vs HUD programs.

### Root cause (two issues)

**Issue A — Map stage over-extracts for summaries**: The map stage for `general_summary` says "Include dollar figures as direct facts only when they directly explain the answer" but in practice extracts all figures as `direct` because the map model is trained to preserve financial detail. The reduce stage then includes all `direct` facts, producing a ledger-like answer.

**Issue B — Retrieval breadth is insufficient for "what does X do" questions**: Summary questions like "What does the Agriculture division do for the FDA?" require broad coverage of provisions, not just the top 12 most semantically similar chunks. The chunks retrieved are likely clustered around the main S&E appropriation, missing peripheral provisions like the electronic prescribing restriction or obligation plan requirement.

### Relevant files

- `app/services/rag_prompting.py` lines 84-89 — `MAP_MODE_PROMPTS["general_summary"]`
- `app/services/rag_prompting.py` lines 228-242 — `REDUCE_MODE_PROMPTS["general_summary"]`
- `app/services/rag_prompting.py` lines 384-397 — `SYNTHESIS_MODE_PROMPTS["general_summary"]`

### Suggested fixes

**For over-detail**: Strengthen the `general_summary` map prompt to demote dollar figures more aggressively. Change "Include dollar figures as direct facts only when they directly explain the answer; otherwise classify them as adjacent" to something like: "For summary questions, classify dollar figures as adjacent unless the question specifically asks about amounts. Extract the provision's purpose and scope as the direct fact, not the dollar figure."

**For breadth**: Consider increasing k for `general_summary` questions, or using a different retrieval strategy (e.g., MMR / maximum marginal relevance) to diversify the chunk set. The current top-12 by cosine similarity tends to cluster around the same section of text.

---

## Finding 6: Annotation markers `[[num:...]]` flagged as internal pipeline language (direct_1, direct_5)

### What happened

The e2e judge flagged `[[num:src_ag_...]]` markers in the final answer as violations of "Should not use internal pipeline language like extracted facts, retrieved facts, mapped facts, or source chunks." This triggered prohibited errors on direct_1 and direct_5, costing points.

### Root cause

The `[[num:...]]` markers are part of the Number Annotation system (see ADR-0006). They are stripped by the frontend before display — users never see them. But the e2e judge evaluates raw pipeline markdown output and has no way to know these are citation markers, not internal language.

### Relevant files

- `tests/evals/e2e/judge.py` — judge system prompt and prompt construction
- `app/services/rag/state.py` lines 15-19 — `NUMBER_MARKER_PATTERN` regex

### Suggested fix (two options)

**Option A (recommended)**: Strip `[[num:...]]` markers from the final answer before sending to the judge. Add to `tests/evals/e2e/run.py` before the judge call:

```python
import re
clean_answer = re.sub(r'\[\[num:[A-Za-z0-9_-]+\]\]', '', entry["final_answer"])
```

This is the right approach because the judge should evaluate content quality as the user would see it, not raw pipeline internals.

**Option B**: Add a note to the judge system prompt: "The answer contains `[[num:...]]` citation markers used by the frontend display system. These are not internal pipeline language — ignore them when checking for internal language violations."

---

## Finding 7: broad_5 missed major cleanup accounts (4/10)

### What happened

`broad_5` asks about brownfields/Superfund/remediation funding. The answer correctly identified Hazardous Substance Superfund ($282.7M) and CERCLA section 128 grants ($46.25M), but missed:
- CERCLA section 104(k) brownfields grants: $98,000,000
- Superfund-related activities under CERCLA 311(a) and 126(g): $77,100,000
- Leaking Underground Storage Tank Trust Fund: $88,903,000 ($64,583,000 for cleanup)
- Brownfields fee authority under CERCLA section 3024

### Root cause

Similar to broad_2: either retrieval didn't surface these chunks (they're spread across different sections of the Interior/Environment bill text) or the map stage didn't classify them as `direct`. The answer mentioned Environmental Programs and Management ($3.1B) broadly but only noted "administrative costs of the brownfields program" within it — it didn't pull out the specific brownfields grant lines.

### Suggested fix

Same diagnostic approach as broad_2. If retrieval gap, increase k or improve rewrite. If mapping gap, the `broad_topic_total` map prompt needs to better recognize that cleanup/remediation-specific grants are `direct` even when they appear in different sections of the bill.

---

## Eval Infrastructure Notes

### Running the eval

```bash
# Load env vars and use project venv (required for chromadb 1.5.8 compatibility)
set -a && source .env && set +a

# Reference mode (dumps pipeline outputs, no judging)
.venv/bin/python3 -m tests.evals.e2e.run --reference --concurrency 3

# Judge mode (requires gold references in gold_references.py)
.venv/bin/python3 -m tests.evals.e2e.run --concurrency 3

# Single question
.venv/bin/python3 -m tests.evals.e2e.run --questions broad_2 --reference

# Custom config
.venv/bin/python3 -m tests.evals.e2e.run --k 16 --thinking-speed long --concurrency 5
```

### Important: must use `.venv/bin/python3`

The system python has chromadb 0.6.x which causes `KeyError: '_type'` on collection config. The project venv (`.venv/`) has chromadb 1.5.8 which matches the stores. This is documented in `.agents/plans/embedding-eval-suite.md` under Discoveries.

### File layout

```
tests/evals/
├── questions.py                    # 25 EvalQuestion dataclasses (shared by both evals)
├── embedding/                      # existing embedding model eval
│   ├── run.py
│   ├── judge.py
│   ├── report.py
│   └── results/
└── e2e/
    ├── __init__.py
    ├── run.py                      # orchestrator: --reference or --judge mode
    ├── judge.py                    # DeepSeek judge with gold reference grading
    ├── report.py                   # 4-level report generation
    ├── gold_references.py          # 25 GoldReference dataclasses
    └── results/
        └── 2026-05-09_190748/
            ├── report.md
            ├── raw_results.json
            └── findings.md         # this file
```

### Gold reference schema

```python
@dataclass(frozen=True)
class GoldReference:
    required_facts: list[str]       # facts the answer MUST contain
    prohibited_errors: list[str]    # specific mistakes to flag
    expected_answer_mode: str       # expected classify output
    expected_divisions: list[str]   # expected route output
    notes: str = ""                 # freeform context for edge cases
```

### Judge output schema

```python
{
    "fact_checks": [{"fact": str, "found": bool, "evidence": str}],
    "error_checks": [{"error": str, "triggered": bool, "evidence": str}],
    "structural_checks": {"passed": bool, "issues": [str]},
    "overall_score": int,   # 0-10
    "reasoning": str
}
```

---

## Prioritized Remediation Steps

| Priority | Finding | Impact | Effort | Step |
|----------|---------|--------|--------|------|
| 1 | Annotation markers flagged as errors | False positives on 2 questions, easy fix | Low | Strip `[[num:...]]` from answer before judge call in `tests/evals/e2e/run.py` |
| 2 | Route returns [] for abstract CRX questions | Total pipeline failure (0/10) | Low | Add conceptual terms to CRX routing aliases in `app/core/config.py` |
| 3 | Classify misses mechanism mode | Wrong answer structure for 3/5 questions | Medium | Add mechanism examples to classify prompt in `app/services/rag/stages/classify.py` |
| 4 | broad_2 missing $52.5B rental assistance | Largest content gap | Medium | Diagnose retrieval vs mapping; likely needs rewrite query expansion or map prompt adjustment |
| 5 | Reconciliation double-counting | Structural error in 2/5 recon questions | Medium | Strengthen reconciliation reduce prompt with pre-emission validation rule |
| 6 | Summary mode over-produces detail | Wrong answer shape for summary questions | Medium | Adjust general_summary map prompt to demote dollar figures more aggressively |
| 7 | broad_5 missing cleanup accounts | Major content gap | Medium | Same diagnosis as broad_2 — retrieval breadth or map-stage classification |
