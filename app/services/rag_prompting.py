"""Prompt modules for LawSearch RAG generation stages."""

from __future__ import annotations

from typing import Any, Literal

AnswerMode = Literal[
    "direct_account_amount",
    "broad_topic_total",
    "funding_mechanism_no_amount",
    "reconciliation_breakdown",
    "general_summary",
]

DEFAULT_ANSWER_MODE: AnswerMode = "broad_topic_total"
ANSWER_MODES: tuple[str, ...] = (
    "direct_account_amount",
    "broad_topic_total",
    "funding_mechanism_no_amount",
    "reconciliation_breakdown",
    "general_summary",
)


INVARIANT_RULES = """Invariant source and accounting rules:
- Preserve source, citation, and [[num:...]] number markers exactly where they belong.
- Do not invent facts, dollar figures, or totals.
- Use only retrieved facts.
- Only sum comparable additive amounts in the same scope.
- Preserve caveats for transfers, rescissions, caps, fees, set-asides, suballocations, limitations, and non-comparable accounts.
- Do not substitute unrelated dollar figures when the requested topic lacks a dollar amount.
- Distinguish funding-mechanism evidence from dollar-figure evidence."""


MAP_BASE_RULES = """Map extraction rules:
- Extract only facts that help answer the question.
- Relevance must be tied to the agency, account, program, authority, or topic in the question, not just the same division or catch-all source bucket.
- Return fact-level responsiveness tiers: direct, adjacent, or not_responsive.
- Use direct only when the fact directly answers the user's topic and scope.
- Use adjacent when the fact is related but not clearly within the user's requested scope.
- Use not_responsive when the fact was retrieved but should not be used to answer the question.
- A single chunk may contain a mix of direct, adjacent, and not_responsive facts; classify each fact separately.
- Preserve exact dollar figures, account names, agencies, fiscal years, and section references.
- Preserve financial-type language around each dollar figure, such as account total, suballocation, grant, direct loan authority, guaranteed loan authority, loan subsidy cost, user fee, offsetting collection, transfer, rescission, set-aside, cap, or limitation.
- Preserve relationship language such as 'of which', 'to remain available', 'derived from fees', 'transferred', 'rescinded', 'not to exceed', and 'loan authority'.
- If the chunk has relevant funding-mechanism evidence but no relevant dollar figure, extract that mechanism as a fact without a source_numbers item.
- Funding-mechanism evidence includes continuing appropriations, rate-for-operations language, apportionment authority, extensions, and referenced prior laws.
- Do not extract unrelated dollar figures merely because the question asks how much; unrelated figures must not be used as substitutes for missing topic-specific amounts.
- One fact per bullet; no paragraphs.
- End every substantive bullet with the citation marker.
- Add one source_numbers item for each relevant dollar figure used in extracted_facts.
- Each source_numbers item must include the exact displayed figure, normalized dollar value, and a short account/program label.
- If the chunk has no relevant evidence, return exactly: - No relevant facts found."""


MAP_EXAMPLE = """Map example:
Question: What amount is appropriated for FDA Salaries and Expenses?
Relevant chunk text says the FDA Salaries and Expenses account receives $6,957,972,000 and nearby Sec. 776 provides $3,000,000 for a separate purpose.
Good fact object: responsiveness_tier=direct, fact="- FDA Salaries and Expenses is appropriated $6,957,972,000 for necessary FDA expenses. [AG]"
The nearby $3,000,000 should be adjacent or not_responsive unless it directly answers the question."""


REDUCE_MODE_PROMPTS: dict[str, str] = {
    "direct_account_amount": """Direct account reduce prompt:
- Use only Direct facts to answer. Use Adjacent facts only for one short scope note when necessary. Do not use Not responsive facts in the answer.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Do not invent facts, dollar figures, or totals. If the facts do not answer the question, say that directly.
- Answer the specific account/program question directly and compactly.
- Default shape: main amount first, then 1 short paragraph. When summarizing multiple major allowed-use categories, use a short bullet list for readability.
- Identify the account, give the main appropriation amount, and summarize major allowed uses when asked.
- For "major allowed uses", summarize categories of use; do not list every center, activity, rent line, transfer, limitation, or user-fee amount unless the user asks for a detailed allocation, breakdown, or reconciliation.
- For "major allowed uses", name categories only. Do not attach dollar figures to internal centers, activities, rent lines, or other suballocations unless the user asks for allocation, breakdown, line items, or "how much for each".
- Separate internally: main appropriation amount, suballocations within that amount, user fees credited to the account, separate provisions outside the account, and limitations/transfers.
- Surface only categories needed to answer the user.
- Mention user fees as credited to the account only when useful for clarity; do not list each user-fee dollar amount unless the user asks for user fees or a funding-source breakdown.
- Do not create Included / Not added separately sections unless the user asks for reconciliation/breakdown or excluding a specific amount is necessary to prevent likely double counting.
- Prefer one concise caveat sentence over a ledger-style excluded-amount section.
- Do not include nearby provisions merely because they were retrieved.
- If you repeat or restate a marked dollar figure, repeat the same [[num:...]] marker immediately after every occurrence of that same figure.
- For any calculated total, add a new marker like [[num:drv_direct_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.

Direct account example:
Question: What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?
Facts include $6,957,972,000 for FDA Salaries and Expenses, necessary FDA expenses including passenger motor vehicles, space rental and related costs, special-purpose space, and emergency enforcement, program/center activities such as Human Foods, CDER, CBER, CVM, CDRH, NCTR, and Center for Tobacco Products, user fees credited to the account, and a separate nearby $3,000,000 provision.
Good answer pattern: Give the $6,957,972,000 account amount, then write "Major allowed uses include:" followed by category-only bullets such as Human Foods Program and related field activities; inspections, investigations, and import operations; CDER; CBER; CVM; CDRH; NCTR; Center for Tobacco Products; rent and related activities; and other central FDA offices and services. Mention that user fees are credited to the account under applicable laws only if useful for clarity. Do not list every center suballocation, do not include center-by-center dollar figures, do not list individual user-fee dollar figures, do not include the separate nearby $3,000,000 provision, and do not create a "Not added separately" section unless the user asks for a breakdown or reconciliation.
Bad answer pattern: "Human Foods Program $1,171,319,000; CDER $2,496,766,000; CBER $601,291,000..." unless the user asks for allocations.
Bad answer pattern: "Prescription drug user fees $1,556,039,000; medical device user fees $478,166,000..." unless the user asks for a user-fee breakdown.""",
    "broad_topic_total": """Broad topic total reduce prompt:
- Use only Direct facts for substantive answer content. Use Adjacent facts only for short not-included or scope notes. Do not use Not responsive facts in the answer.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Do not invent facts, dollar figures, or totals. If the facts do not answer the question, say that directly.
- Output a compact division brief for synthesis, not a full ledger.
- Default shape for divisions with direct evidence: Bottom line: <1 sentence naming the controlling agency/account(s) and whether a clean total is available>; Key buckets: <2-4 bullets max, grouped by controlling agency/account/program>; Local caveat: <optional 1 sentence only if needed to prevent double counting>.
- Use one bullet per controlling account/program. Do not create separate bullets for suballocations within the same parent account.
- Include only top-level amounts and the most decision-useful sub-buckets. Omit tiny sub-set-asides, internal earmarks, administrative amounts, and repeated duplicate figures unless the user asks for detail.
- Provide a "total found" only when top-level comparable additive buckets are present in the same scope.
- Do not compute or lead with a mixed identified total unless the user explicitly asks for a summed identified amount.
- If figures mix financial types or hierarchy is unclear, lead with grouped buckets instead of one clean headline total.
- Before aggregating, classify each amount internally by financial type and additive relationship: account total, suballocation, grant, direct loan authority, guaranteed loan authority, loan subsidy cost, user fee, offsetting collection, transfer, rescission, set-aside, cap, or limitation.
- Do not add account totals plus suballocations, loan authority plus loan subsidy cost, user fees plus account totals, transfers as new funding, rescissions as positive funding, or set-asides inside a broader amount unless the user specifically asks for that category and the facts support the relationship.
- For routed divisions with no Direct facts, return only the heading plus one no-direct-info sentence using the best Adjacent reason.
- If you repeat or restate a marked dollar figure, repeat the same [[num:...]] marker immediately after every occurrence of that same figure.
- For any calculated comparable total, add a new marker like [[num:drv_broad_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.

Broad total example:
Question: how much for FEMA?
Facts include FEMA operations and support $1,483,990,000, FEMA procurement/construction/improvements $99,528,000, FEMA Federal Assistance $3,497,019,369, Disaster Relief Fund $20,261,000,000, National Flood Insurance Fund $239,983,000, and a $33,000,000 transfer to FEMA Federal Assistance.
Good answer pattern: Start with "FEMA total found: $25,581,520,369" when adding those retrieved top-level comparable buckets. Include operations/support, procurement/construction/improvements, Federal Assistance, Disaster Relief Fund, and National Flood Insurance Fund. Do not add the $33,000,000 transfer separately.

Mixed financial types example:
Question: What FY2026 funding is available for rural water/wastewater infrastructure?
Facts include USDA Rural Utilities Service direct loan authority $X, USDA Rural Utilities Service guaranteed loan authority $Y, USDA Rural Utilities Service subsidy/grant/program funding $Z, USDA technical assistance/circuit rider funding $A, and EPA targeted grant funding $B.
Good answer pattern: For USDA RUS, use one Rural Water and Waste Disposal Program Account bullet that names direct loan authority, guaranteed loan authority, and program-cost/grant funding. Mention key technical-assistance or grant buckets compactly only if they materially help the user locate the funding. Do not split every section 306 set-aside into separate bullets. Do not present direct loans plus guarantees plus grants as one clean total.""",
    "funding_mechanism_no_amount": """Funding mechanism reduce prompt:
- Use only Direct facts to answer. Use Adjacent facts only for one short scope note when necessary. Do not use Not responsive facts in the answer.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Do not invent facts, dollar figures, or totals.
- Distinguish dollar-figure evidence from funding-mechanism evidence.
- Continuing appropriations, rate-for-operations language, apportionment authority, extensions, and referenced prior laws can explain how funding continues, but they are not dollar amounts.
- If the requested topic has funding-mechanism evidence but no relevant dollar figure, say that a dollar total was not found in the extracted facts and explain what mechanism was found.
- If answering the dollar amount requires a prior-year baseline or referenced law that is not present in the extracted facts, say that explicitly.
- Do not substitute unrelated dollar figures from the same division or source bucket.
- Do not create Included / Not added separately sections, totals, or reconciliation tables.
- Keep the response compact: one bottom-line sentence plus up to 3 mechanism bullets when useful.
- If you repeat or restate a marked dollar figure, repeat the same [[num:...]] marker immediately after every occurrence of that same figure.
- For any calculated total, add a new marker like [[num:drv_mechanism_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.

Funding mechanism example:
Question: how much money for FEMA?
Facts include that amounts made available by continuing appropriations to the Department of Homeland Security under "Federal Emergency Management Agency--Disaster Relief Fund" may be apportioned up to the rate for operations necessary for Stafford Act response and recovery. Facts also include unrelated Indian Health Service amounts.
Good answer pattern: Say "FEMA total found: no FEMA-specific dollar amount identified in the extracted facts." Then explain that the retrieved text provides funding-mechanism evidence for continuing/apportioning Disaster Relief Fund operations, but no explicit FEMA dollar figure. Omit unrelated Indian Health Service amounts as not responsive.""",
    "reconciliation_breakdown": """Reconciliation and breakdown reduce prompt:
- Use Direct facts for substantive answer content. Use Adjacent facts only for short not-included or scope notes. Do not use Not responsive facts in the answer.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Do not invent facts, dollar figures, or totals. If the facts do not answer the question, say that directly.
- Use Included / Not added separately structure when the user asks for a breakdown, combined total, reconciliation, show math, included/excluded amounts, double-counting analysis, comparison, or multiple named topics.
- For combined-topic questions, provide one total found per topic and a combined total found only when those topic totals are clearly additive.
- Preserve enough detail to audit the math.
- If a broader parent account and one of its components both appear, include the parent account and explain that the component was not added separately.
- Group breakdown bullets under their topic instead of writing one flat accounts list.
- Classify excluded amounts by relationship: suballocation, transfer, fee/offset, cap/limitation, rescission, administrative amount, component, or unknown.
- Put excluded transfer, cap, administrative amount, component, or related figure under the relevant topic's Not added separately subsection rather than creating a new topic section.
- Do not add account totals plus suballocations, loan authority plus loan subsidy cost, user fees plus account totals, transfers as new funding, rescissions as positive funding, or set-asides inside a broader amount unless the user specifically asks for that category and the facts support the relationship.
- If figures are mixed but the user asked for reconciliation, preserve the math and label any cross-type arithmetic as a mixed identified total, not a clean funding pool.
- If you repeat or restate a marked dollar figure, repeat the same [[num:...]] marker immediately after every occurrence of that same figure.
- For any calculated total, add a new marker like [[num:drv_recon_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.

Reconciliation example:
Question: how much for FEMA and immigration combined?
Facts include FEMA Federal Assistance $3,497,019,369, ICE operations and support $9,501,542,000, ICE enforcement/detention/removal $5,082,218,000, USCIS operations and support $271,140,000, USCIS Citizenship and Integration grants $10,000,000, and CBP operations and support $18,426,870,000.
Good answer pattern: Start with "FEMA total found", "Immigration-related total found", and "Combined FEMA + immigration-related total found" only when the arithmetic is source-backed. Then use separate FEMA and Immigration-related sections. Do not add the ICE enforcement/detention/removal component separately when the broader ICE operations/support amount is included.""",
    "general_summary": """General summary reduce prompt:
- Use only Direct facts for substantive answer content. Use Adjacent facts only for one short scope note when necessary. Do not use Not responsive facts in the answer.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Do not invent facts, dollar figures, or totals. If the facts do not answer the question, say that directly.
- Answer the user's question directly using the retrieved facts.
- Keep the answer concise and explanatory, usually 1-3 short paragraphs or up to 5 bullets.
- Include dollar figures only when they directly explain the answer.
- Do not turn a non-numeric question into a reconciliation ledger.
- Do not create Included / Not added separately sections unless the user explicitly asks for accounting.
- If you repeat or restate a marked dollar figure, repeat the same [[num:...]] marker immediately after every occurrence of that same figure.
- For any calculated total, add a new marker like [[num:drv_summary_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.

General summary example:
Question: What does this division do for FDA facilities?
Good answer pattern: Summarize the directly relevant provisions and cite retrieved facts. Include amounts only if they directly explain the answer.""",
}


SYNTHESIS_MODE_PROMPTS: dict[str, str] = {
    "direct_account_amount": """Direct account synthesis prompt:
Use this markdown structure:
## Answer
<main account amount and short use summary>

## Source Scope
- **[ACRONYM]:** <why this division is the direct source, or one-line note if it was routed but not direct>

Rules:
- Use only the division answers. Do not invent facts, dollar figures, or totals.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Keep the final answer compact: main amount first, then 1-2 short paragraphs or up to 4 bullets for requested uses/context.
- Do not introduce By Agency / Account, Included, or Not added separately sections.
- Do not list every suballocation, center, activity, rent line, transfer, limitation, or user-fee amount unless the user asked for that detailed breakdown.
- If more than one division has competing direct answers, say that clearly instead of merging them.
- Routed divisions with no direct evidence should appear only as one-line Source Scope notes.
- For any calculated total, add a new marker like [[num:drv_final_direct_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.""",
    "broad_topic_total": """Broad topic synthesis prompt:
Use this markdown structure. Only include sections that have content.

## Answer
<1 short paragraph. State whether a clean total is available and name the main controlling agencies/accounts. Do not use internal pipeline words like "division answers", "extracted facts", "retrieved facts", or "provided facts".>

## Topic-Specific or Targeted Funding
### <Agency/account/program> [ACRONYM]
- <Financial type>: <amount and short description>
- <Financial type>:
  - <subtype>: <amount>
  - <subtype>: <amount>
- Key identified suballocations within/under this account:
  - <suballocation/set-aside>: <amount>

## Broader Related Funding
### <Agency/account/program> [ACRONYM]
- <Financial type>: <amount and short description>

## Identified But Not Cleanly Topic-Specific
### <Agency/account/program> [ACRONYM]
- <why it is related but not cleanly within the user's requested scope>

## Not Included
- **<Division/acronym>:** <one-line reason when a routed division has no direct responsive funding or only adjacent material.>

## Caveats
- <2-4 bullets max. Only caveats needed to prevent misreading or double counting.>

Rules:
- Use only the division answers. Do not invent facts, dollar figures, or totals.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Do not mention "division answers", "extracted facts", "retrieved facts", "provided facts", or other pipeline/internal process language in the final answer.
- Use these section titles exactly when applicable: "Topic-Specific or Targeted Funding", "Broader Related Funding", "Identified But Not Cleanly Topic-Specific", "Not Included", and "Caveats".
- Do not generate long topic-expanded section names like "Rural Water or Wastewater-Specific or Rural Water or Wastewater-Targeted Funding".
- For broad mixed-financial-type questions, organize by specificity before account detail: topic-specific or targeted funding; broader related funding that may support relevant projects; identified but not cleanly topic-specific; not included.
- Only include sections that have content.
- Do not append full division answers. Combine already-shaped division results.
- Do not create multiple top-level bullets or headings for the same agency/account/heading. Use one heading per controlling account and nest financial types, suballocations, and set-asides underneath it.
- Preserve direct subamounts that help the user identify funding sources, but nest them under the controlling account instead of making them separate top-level accounts.
- Use valid markdown bullets for all account details and nested amounts. Indent nested bullets by two spaces.
- Label each amount by financial type where possible: appropriated cost/grant/subsidy, direct loan authority, guaranteed loan authority, grant reservation, administrative expenses, suballocation/set-aside, transfer, cap/limitation, rescission, or user fee.
- Do not repeat the same agency, account, bucket, or dollar figure in both the top Answer and the detailed sections.
- Do not drop a routed division; if it has no direct evidence, put it in Not Included as one line.
- Provide a clean total only when amounts are comparable and additive in the same scope.
- Do not compute or lead with a mixed identified total unless the user explicitly asks for a summed identified amount.
- Do not add account totals plus suballocations, loan authority plus loan subsidy cost, user fees plus account totals, transfers as new funding, rescissions as positive funding, or set-asides inside a broader amount unless the user specifically asks for that category and the facts support the relationship.
- Caveats must be cross-cutting only. Put local hierarchy or double-counting notes beside the relevant account.
- For any calculated total, add a new marker like [[num:drv_final_broad_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.

Good pattern:
### USDA Rural Utilities Service — Rural Water and Waste Disposal Program Account [AG]
- Appropriated cost/grant/subsidy: $445,864,564
- Loan authority:
  - Direct loans: $1,015,000,000
  - Guaranteed loans: $50,000,000
- Key identified suballocations within/under this account:
  - Section 306(a)(2)(A) grants: $250,488,564
  - Technical assistance grants: $35,000,000

Bad pattern:
- USDA RUS — same account/heading [AG]: ...
- USDA RUS — section 306(a)(2)(A) grants [AG]: ...
- USDA RUS — technical assistance and rural utilities support [AG]: ...""",
    "funding_mechanism_no_amount": """Funding mechanism synthesis prompt:
Use this markdown structure:
## Answer
<no explicit amount found / mechanism found>

## Mechanism Found
- **[ACRONYM]:** <continuing appropriation, rate-for-operations, extension, apportionment authority, or prior-law reference>

## Missing Amount
- <what would be needed to calculate or identify a dollar amount>

Rules:
- Use only the division answers. Do not invent facts, dollar figures, or totals.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Do not include unrelated dollar figures from routed divisions.
- Do not create totals, Included sections, Not added separately sections, or reconciliation tables.
- If no direct dollar figure exists, say that no explicit dollar amount was found in the retrieved facts.
- Explain the funding mechanism found, such as continuing appropriation, rate-for-operations, apportionment authority, extension, or referenced prior law.
- If a prior-year baseline or referenced law is required to calculate a dollar amount, say that explicitly.
- Routed divisions with no direct evidence should be omitted unless needed as a one-line missing-scope note.
- For any calculated total, add a new marker like [[num:drv_final_mechanism_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.""",
    "reconciliation_breakdown": """Reconciliation synthesis prompt:
Use this markdown structure:
## Answer
<totals found and combined total only if supported>

## Included
- **<topic/account> [ACRONYM]:** <amount and why included>

## Not Added Separately
- **<topic/account> [ACRONYM]:** <amount and why excluded>

## Caveats
- <math, comparability, or hierarchy caveats needed to audit the answer>

Rules:
- Use only the division answers. Do not invent facts, dollar figures, or totals.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Preserve enough detail to audit the math.
- Use Included / Not Added Separately because this mode is for breakdowns, reconciliation, comparisons, and double-counting analysis.
- Show combined totals only when topic totals are clearly additive.
- Identify parent totals, suballocations, transfers, fees/offsets, caps/limitations, rescissions, administrative amounts, and unknown relationships.
- Do not add account totals plus suballocations, loan authority plus loan subsidy cost, user fees plus account totals, transfers as new funding, rescissions as positive funding, or set-asides inside a broader amount unless the user specifically asks for that category and the facts support the relationship.
- If cross-type arithmetic is retained for user visibility, label it as a mixed identified total, not a clean funding pool.
- Group excluded caveats under the related topic instead of creating unrelated sections.
- For any calculated total, add a new marker like [[num:drv_final_recon_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.""",
    "general_summary": """General summary synthesis prompt:
Use this markdown structure:
## Answer
<concise prose or short bullets>

Rules:
- Use only the division answers. Do not invent facts, dollar figures, or totals.
- Preserve source, citation, and [[num:...]] markers immediately after the figures or clauses they support.
- Answer the user's question directly and concisely.
- Do not force accounting sections.
- Include dollar figures only when they directly explain the answer.
- Do not turn a summary question into a reconciliation ledger.
- Routed divisions with no direct evidence should appear only as one-line scope notes when useful.
- For any calculated total, add a new marker like [[num:drv_final_summary_1]] immediately after the visible total and add a matching derived annotation whose input_ids reference existing annotations.""",
}


def normalize_answer_mode(mode: str | None) -> AnswerMode:
    """Return a supported answer mode, defaulting to broad topic totals."""
    if mode in ANSWER_MODES:
        return mode  # type: ignore[return-value]
    return DEFAULT_ANSWER_MODE


def mode_flags_text(flags: dict[str, Any] | None) -> str:
    """Format selected answer-mode flags for prompts."""
    flags = flags or {}
    active = [key for key, value in flags.items() if value]
    return ", ".join(active) if active else "none"


def _mode_reduce_prompt(answer_mode: str, flags: dict[str, Any] | None) -> str:
    mode = normalize_answer_mode(answer_mode)
    return "\n".join(
        [
            "Answer-mode instructions:",
            f"- Selected answer_mode: {mode}",
            f"- Active safety flags: {mode_flags_text(flags)}",
            "",
            REDUCE_MODE_PROMPTS[mode],
        ]
    )


def _mode_synthesis_prompt(answer_mode: str, flags: dict[str, Any] | None) -> str:
    mode = normalize_answer_mode(answer_mode)
    return "\n".join(
        [
            "Answer-mode instructions:",
            f"- Selected answer_mode: {mode}",
            f"- Active safety flags: {mode_flags_text(flags)}",
            "",
            SYNTHESIS_MODE_PROMPTS[mode],
        ]
    )


def build_map_prompt(
    *,
    question: str,
    chunk_content: str,
    division_acronym: str,
    answer_mode: str,
    answer_mode_flags: dict[str, Any] | None,
) -> str:
    """Build the map-stage extraction prompt."""
    return (
        "You are a legislative financial analyst extracting evidence from one source chunk.\n\n"
        "Return structured output with `facts`, where each fact has `fact`, `responsiveness_tier`, `reason`, "
        "and `source_numbers` for the dollar figures used in that fact. Legacy `extracted_facts` may be used only "
        "when fact-level objects are unavailable.\n\n"
        "Use this markdown bullet format in extracted_facts:\n"
        "- <specific fact with exact dollar figure/account/program/agency/fiscal year if present> "
        f"[{division_acronym}]\n\n"
        f"Selected answer_mode: {normalize_answer_mode(answer_mode)}\n"
        f"Active safety flags: {mode_flags_text(answer_mode_flags)}\n\n"
        f"{INVARIANT_RULES}\n\n"
        f"{MAP_BASE_RULES}\n\n"
        f"{MAP_EXAMPLE}\n\n"
        f"Question:\n{question}\n\n"
        f"Source chunk:\n{chunk_content}"
    )


def build_reduce_prompt(
    *,
    question: str,
    division: str,
    division_acronym: str,
    answer_mode: str,
    answer_mode_flags: dict[str, Any] | None,
    annotation_context: str,
    facts: str,
) -> str:
    """Build the reduce-stage prompt for one division."""
    return (
        "Synthesize the extracted facts into a division-level answer. "
        "Return structured output with `answer` markdown and `derived_annotations`.\n\n"
        "Answer shape:\n"
        f"- Start with a heading exactly like: ### [{division_acronym}] {division}\n"
        "- Then follow the selected answer-mode prompt exactly.\n\n"
        f"{_mode_reduce_prompt(answer_mode, answer_mode_flags)}\n\n"
        f"Question:\n{question}\n\n"
        f"Division: {division}\n\n"
        f"Available annotations:\n{annotation_context}\n\n"
        f"Tiered extracted facts:\n{facts}"
    )


def build_synthesis_prompt(
    *,
    question: str,
    answer_mode: str,
    answer_mode_flags: dict[str, Any] | None,
    annotation_context: str,
    division_context: str,
) -> str:
    """Build the final synthesis prompt for multi-division answers."""
    return (
        "Create the final answer from the division-level answers. "
        "Return structured output with `answer` markdown and `derived_annotations`.\n\n"
        f"{_mode_synthesis_prompt(answer_mode, answer_mode_flags)}\n\n"
        f"Question:\n{question}\n\n"
        f"Available annotations:\n{annotation_context}\n\n"
        f"Division answers:\n{division_context}"
    )
