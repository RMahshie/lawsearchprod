# Gold Reference Audit — 2026-07-16

## Executive verdict

The Gold References are a strong foundation, but they are not yet reliable enough to serve as the authoritative benchmark without correction.

| Verdict | Questions | Meaning |
|---|---:|---|
| Good | 10 | Source-supported and materially adequate for the question |
| Minor issues | 11 | Core is accurate, but incomplete, over-specified, ambiguous, or miscategorized |
| Major issues | 4 | Contains a material factual/scope error or omits a central answer lane |

All 25 eval questions have Gold References. Their expected answer modes align, and expected Divisions match the question definitions as sets. The strongest parts of the suite are its parent/child funding hierarchy checks, financial-type distinctions, and anti-double-counting rules.

The four major defects are:

1. `direct_5` mishandles the VA Medical Services funding tranche and attributes cross-account medical programs solely to Medical Services.
2. `broad_2` omits CDBG and HOME, two central city-facing affordable-housing lanes.
3. `broad_3` requires terminal-upgrade coverage that is not supported by the supplied FY2026 source text.
4. `broad_4` assigns an OJP $84 million police-community-relations lane, including $50 million for community violence intervention, to COPS.

These are not theoretical defects. The latest committed eval penalized source-faithful answers for `direct_5` and `broad_4`, did not measure the CDBG omission in `broad_2`, and gave `broad_3` full credit for mentioning administrative Airport Terminal Program support even though it was not terminal-upgrade construction.

## Scope and method

The audit compared every question, required fact, prohibited error, answer mode, and expected Division against the three authoritative Public Law texts in the repository:

- **PL37** — [P.L. 119-37](../../../data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm)
- **PL74** — [P.L. 119-74](../../../data/bills/2026/FY2026_CommerceJusticeScience_EnergyWaterDev_INTERIOREnvironmental.htm)
- **PL75** — [P.L. 119-75](../../../data/bills/2026/FY2026_CONSOLIDATED.htm)

Seven Luna-high review passes covered the five answer modes, benchmark consistency, and an independent adversarial check of all major findings. Pipeline answers were not used as legal truth. The latest committed results were inspected only to measure whether Gold Reference defects affected scoring.

No Gold Reference, question, judge, or pipeline code was changed during this audit.

## Major findings

### 1. `direct_5`: VA Medical Services year and scope are wrong

The Medical Services heading provides **$59,858,000,000 plus reimbursements**, available from October 1, 2026 through September 30, 2027. It separately identifies **$75,039,000,000** that became available October 1, 2025 and rescinds **$15,889,000,000** from that earlier tranche. See PL37:6511–6537.

The current gold calls $59.858 billion the FY2026 amount without resolving those tranches. That is materially ambiguous for a question asking what is appropriated “in FY2026.”

The required service list is also mis-scoped. Women veterans care, suicide prevention, PTSD, rural health, homelessness, telehealth, opioid treatment, and related programs appear in section 251 as pooled funding across five accounts: Medical Services, Medical Community Care, Medical Support and Compliance, Medical Facilities, and Cost of War Toxic Exposures. They cannot all be attributed solely to Medical Services. See PL37:7601–7622.

Observed impact: the latest answer accurately summarized the direct Medical Services heading but received 6/10 for omitting the pooled cross-account list.

### 2. `broad_2`: central city housing programs are missing

The listed rental-assistance and homelessness facts are accurate, but the gold omits two central responses to a city seeking affordable-housing funding:

- Community Development Fund: **$6,995,244,120**, including **$3,300,000,000 for CDBG** available to States and units of general local government. See PL75:13191–13227.
- HOME Investment Partnerships: **$1,250,000,000**. See PL75:13325–13340.

Choice Neighborhoods and Housing for the Elderly are additional responsive lanes, but CDBG and HOME are the material omissions. A system can satisfy the current gold while giving a city an incomplete answer.

Observed impact: the latest answer included HOME, but the judge could neither reward it as a required fact nor flag the missing CDBG lane.

### 3. `broad_3`: unsupported terminal-upgrade requirement

The airport amounts and hierarchy are accurate: $4 billion for airport planning/development and safety, plus a separate $577.356 million heading containing $542.356 million in CPF/CDS and up to $35 million in discretionary grants. See PL75:9624–9717.

The corpus does not provide an affirmative terminal-upgrade construction amount. “Airport Terminal Program” appears as the source of a **$68.67 million transfer from unobligated administrative balances** for personnel, contracting, and oversight—not terminal construction. See PL75:9752–9754. Another terminal reference restricts baggage-conveyor or terminal-baggage reconfiguration work. See PL75:9650–9652.

The prohibited error “Should not omit runway improvements or terminal upgrades” therefore pressures answers to claim support that the supplied source does not establish.

Observed impact: the latest answer carefully called the $68.67 million administrative support rather than construction, but the judge treated that mention as satisfying terminal-upgrade coverage and awarded 10/10.

### 4. `broad_4`: OJP funding is attributed to COPS

The **$84 million** police-community-relations initiative, including **$50 million** for community violence intervention and prevention, is under OJP's $2.4 billion State and Local Law Enforcement Assistance heading. See PL74:1444–1494 and 1694–1708.

COPS is a separate **$800 million** heading containing $253,093,613 for hiring, $32 million for Tribal law enforcement, $18 million for community policing development, $15 million for de-escalation, and other lines. See PL74:1816–1912.

The gold incorrectly says COPS contains the $84 million and $50 million OJP lines. This directly contradicts the expected grouped-by-account answer shape.

Observed impact: the latest answer correctly kept the $84 million lane separate from COPS; the judge marked both false gold facts as missing and scored the answer 5/10.

## Per-question results

### Direct account amount

| ID | Verdict | Audit conclusion | Primary evidence |
|---|---|---|---|
| `direct_1` | Good | FDA total, major activities, fee credits, and non-addition rules are supported. | PL37:2554–2684 |
| `direct_2` | Minor | Amount and authorities are correct; the humane-slaughter provision is a 148-FTE staffing proviso, not best framed as a generic “major activity.” | PL37:1342–1365 |
| `direct_3` | Good | NASA Science amount, purpose, availability date, and CJS scope are supported. | PL74:2144–2165 |
| `direct_4` | Minor | Main EPM facts are correct, but the required set-asides are over-strict for a compact answer; the gold also omits a $20 million Alaska program and separate $9 million TSCA amount. | PL74:7297–7379 |
| `direct_5` | **Major** | FY/tranche ambiguity and cross-account service misattribution make the current gold unsafe. | PL37:6511–6537, 7601–7622 |

### Broad topic total

| ID | Verdict | Audit conclusion | Primary evidence |
|---|---|---|---|
| `broad_1` | Good | USDA, EPA, WIFIA, and EWD authorization facts and financial-type cautions are accurate. | PL37:2077–2153; PL74:4187–4199, 7466–7819 |
| `broad_2` | **Major** | Listed facts are accurate, but CDBG and HOME are central omissions for a city-facing answer. | PL75:12388–13664 |
| `broad_3` | **Major** | Airport funding facts are accurate; mandatory terminal-upgrade coverage is unsupported. | PL75:9624–9754 |
| `broad_4` | **Major** | OJP $84 million/$50 million lines are incorrectly assigned to COPS. | PL74:1444–1912 |
| `broad_5` | Good | Superfund, brownfields, LUST, EPM, and fee-authority distinctions are supported. | PL74:7297–7901, 8762–8766 |

### Funding mechanism with no amount

| ID | Verdict | Audit conclusion | Primary evidence |
|---|---|---|---|
| `mechanism_1` | Good | DHS CR mechanism, FY2025 rate, February 13 extension, and scoped no-full-year-total claim are supported. | PL37:105–222; PL75:27241–27277 |
| `mechanism_2` | Minor | Core mechanism is correct, but required facts omit the exact February 13 date and explicit no-new-total conclusion expected by the question definition. | PL37:105–174; PL75:27241–27277 |
| `mechanism_3` | Good | FEMA DRF apportionment, Stafford scope, extension, designations, and no-explicit-total finding are supported. | PL37:114–127, 246–250, 636–648; PL75:27241–27277 |
| `mechanism_4` | Minor | No CISA-specific amount is supported by a full corpus sweep, but the files do not name CISA; several required claims should be labeled as inference from the generic CR mechanism. | PL37:114–127, 643–657 |
| `mechanism_5` | Minor | Core CR rules are correct, but “all agencies/accounts without full-year funding continue” is too broad; apportionment and no-new-amount conclusions are missing. | PL37:114–222, 296–361 |

### Reconciliation breakdown

| ID | Verdict | Audit conclusion | Primary evidence |
|---|---|---|---|
| `recon_1` | Good | All FDA allocations, fee sources, floors, caps, transfers, and arithmetic are supported. | PL37:2560–2667 |
| `recon_2` | Minor | NASA facts are accurate, but the gold omits the positive conclusion that the nine top-level accounts can sum to $24,438,336,000; its “conflicting explanatory statement” instruction has no conflict in the available source. | PL74:2144–2380 |
| `recon_3` | Good | USDA loan authority, subsidy/grant funding, nested lines, transfer, caps, and derived totals are supported. | PL37:2075–2170, 3240–3247 |
| `recon_4` | Minor | Figures are supported, but $20.364 million is a broader STAG remediation/construction/environmental-management lane, not expressly water infrastructure; one structural prohibition is misfiled as a required fact. | PL74:7466–7758 |
| `recon_5` | Minor | IRS amounts are accurate, but the gold omits the requested conclusion: no statutory parent total is stated; the three top-level accounts arithmetically sum to $11,195,365,000. The BSM finding is absence-based. | PL75:15748–16078 |

### General summary

| ID | Verdict | Audit conclusion | Primary evidence |
|---|---|---|---|
| `summary_1` | Minor | Facts are true, but obscure obligation-plan and e-prescribing riders are mandatory while core FDA inspection/regulatory activities are not. | PL37:2554–2655, 3069–3094 |
| `summary_2` | Minor | Listed domains are supported, but the gold is detail-heavy and omits major DOE Science, NNSA, and Corps domains. | PL74:3474–5209 |
| `summary_3` | Minor | USDA/EPA/Reclamation facts are supported; Corps civil water infrastructure is a material EWD omission. | PL37:2075–2147; PL74:3490–4201, 7466–7818 |
| `summary_4` | Good | Regular-versus-continuing distinction and CR mechanics are fair and source-supported. | PL37:105–222, 305–312; PL75:27246–27267 |
| `summary_5` | Good | Transportation, local-government, HUD, housing, and distinct-account coverage are materially adequate. | PL75:8780–13656 |

## Cross-cutting benchmark weaknesses

### 1. Gold facts have no source provenance

`GoldReference` stores only free-text facts, prohibited errors, expected mode/Divisions, and notes. It has no Public Law, Bill Division, section/page, Chunk, source excerpt/hash, verification status, reviewer, or scoped corpus field.

That is especially risky for absence claims such as “no amount appears.” Those claims are valid only against a named and complete source scope. The newly added Number Annotation provenance check validates generated answers; it does not establish that the Gold References themselves are correct.

### 2. Fact recall is not comparably weighted

The suite contains **217 required facts** and **115 prohibited errors**, but required-fact counts range from 3 to 27 per question.

- Reconciliation questions contribute 94/217 facts (**43.3%**) despite being 5/25 questions.
- Broad-topic questions contribute 51/217 (**23.5%**).
- A major account total and a minor $20,000 reception cap each receive one binary fact check.
- Some long compound facts contain ten or more assertions but still receive one binary result.

The current global Fact Recall is therefore a micro-average dominated by highly atomized reconciliation golds, not an equal view of question quality.

### 3. Facts, guardrails, and style rules are mixed

At least three `required_facts` are actually response rules, such as “the answer should not provide a derived subtotal” or “the answer should be concise.” Similar constraints are repeated in `prohibited_errors` and the judge's mode-specific structural rules, allowing one mistake to affect several scoring dimensions.

The judge also selects structural rules using the **actual classified mode**, not the expected mode. A classification miss can therefore be evaluated with the wrong answer-shape rubric.

### 4. Latest committed metrics predate provenance checking

The latest committed run, `2026-05-13_214032`, contains 25 results but no provenance records. Its 7.7/10 average and 81.1% Fact Recall should not be described as provenance-verified, and the four major Gold Reference defects make the affected question scores unsuitable as a clean baseline.

### 5. Duplicate editable gold artifact

`gold_references.md` is an exact copy of the Python dictionary body, not generated documentation. Only `gold_references.py` is imported. The two files currently match but have no synchronization check, creating avoidable drift risk.

### 6. Route coverage is exact and imbalanced

Route success requires exact set equality, with no partial-credit or acceptable-extra-Division model. Division coverage is also uneven: AG appears in seven questions and CRX in six, while MCVA and FSGG appear once each. This is acceptable for a targeted benchmark but should not be presented as balanced Division-wide routing coverage.

## Recommended improvement order

The findings below were the recommended order at audit time:

1. Correct the four major question/gold defects before using the suite for model comparisons.
2. Add source-linked, typed fact records with verification metadata and explicit corpus scope for absence claims.
3. Separate required facts, prohibited factual errors, structural rules, and allowed alternatives.
4. Give facts importance tiers or weights and report macro per-question/per-mode results alongside micro Fact Recall.
5. Address the 11 minor question-specific issues, then rerun the full benchmark with deterministic provenance enabled.
6. Remove or generate the duplicate `.md` artifact and add schema validation for judge output.

## Implementation status — 2026-07-16

The follow-up implementation resolves the four major and eleven minor findings recorded above:

- all scored facts now have stable IDs, weights, fact types, verification status, and checked-in source-file/range/anchor evidence protected by bill hashes;
- absence claims name a complete corpus scope and search target, while derived claims carry explicit equations;
- the VA tranche, CDBG/HOME, airport-terminal, OJP/COPS, CR, NASA, IRS, EPA, FDA, DOE/NNSA, and Corps findings were corrected or pruned as recommended;
- factual errors and custom answer-shape rules are separate, while routing is evaluated from `expected_divisions` rather than duplicated in the semantic judge;
- judge output is schema-validated, retried on malformed output, and checked for the exact expected criterion IDs using the expected Answer Mode rubric;
- reports retain historical micro Fact Recall and add weighted micro, macro per-question/per-mode, and route precision/recall/F1 diagnostics;
- `gold_references.py` is the sole editable Gold Reference source; the duplicated `gold_references.md` was removed.

Focused validation covers the schema, all audited corrections, judge retry/strictness, historical report compatibility, route diagnostics, and deterministic Number Annotation provenance. A new paid live benchmark has not been run, so the May results remain historical and should not be compared directly with future scores without noting the changed Gold References.

## Bottom line

The benchmark has good domain instincts and catches real legal-RAG failure modes, especially financial-type mixing and double counting. Most individual statutory amounts checked out. Its present weakness is that several Gold References are incomplete or materially wrong while the schema provides no durable evidence trail. Correcting the four major cases and making every gold fact source-verifiable should come before tuning the RAG system against these scores.
