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


MODE_REDUCE_RULES: dict[str, str] = {
    "direct_account_amount": """Direct account answer rules:
- Answer the specific account/program question directly and compactly.
- Identify the account, give the main amount, and summarize major allowed uses when asked.
- Separate internally: main appropriation amount, suballocations within that amount, user fees credited to the account, and separate provisions outside the account.
- Surface only categories needed to answer the user.
- Do not create a "Not added separately" section unless the user asks for reconciliation/breakdown or excluding an amount is necessary to prevent double counting.
- Do not include nearby provisions merely because they were retrieved.
- Do not include long suballocation or user-fee detail unless the user asks for that breakdown or it is essential to answer accurately.""",
    "broad_topic_total": """Broad topic total rules:
- For broad topic questions, provide a "total found" only when top-level comparable additive buckets are present.
- If the facts are mixed or hierarchy is unclear, lead with grouped buckets instead of one clean headline total.
- For questions spanning agencies, components, accounts, or programs, break the answer down by those units by default.
- Every calculated total must state exactly what is included and what was not added separately.
- If a total is provisional because hierarchy is ambiguous, label it as a retrieved top-level bucket total and explain the ambiguity.""",
    "funding_mechanism_no_amount": """Funding mechanism answer rules:
- Distinguish dollar-figure evidence from funding-mechanism evidence.
- Continuing appropriations, rate-for-operations language, apportionment authority, extensions, and referenced prior laws can explain how funding continues, but they are not dollar amounts.
- If the requested topic has funding-mechanism evidence but no relevant dollar figure, say that a dollar total was not found in the extracted facts and explain what mechanism was found.
- If answering the dollar amount requires a prior-year baseline or referenced law that is not present in the extracted facts, say that explicitly.
- Do not substitute unrelated dollar figures from the same division or source bucket.""",
    "reconciliation_breakdown": """Reconciliation and breakdown rules:
- Use Included / Not added separately structure when the user asks for a breakdown, combined total, reconciliation, show math, included/excluded amounts, double-counting analysis, comparison, or multiple named topics.
- For combined-topic questions, provide one total found per topic and a combined total found only when those topic totals are clearly additive.
- If a broader parent account and one of its components both appear, include the parent account and explain that the component was not added separately.
- Group breakdown bullets under their topic instead of writing one flat accounts list.
- If an excluded transfer, cap, administrative amount, component, or related figure belongs to the requested topic only as a caveat, put it under that topic's Not added separately subsection rather than creating a new topic section.""",
    "general_summary": """General summary rules:
- Answer the user's question directly using the retrieved facts.
- Keep the answer concise and explanatory.
- Include dollar figures only when they are directly relevant to the question.
- Do not turn a non-numeric question into a reconciliation ledger.""",
}


MIXED_FINANCIAL_TYPE_RULES = """Mixed financial-type safety rules:
- Before aggregating dollar figures, classify each amount internally by financial_type, scope/account/program, additive_relationship, and include_in_headline_total.
- Use additive_relationship values such as additive, suballocation, offset/fee, transfer, rescission, cap/limitation, or unknown.
- Treat unknown as not safe for a headline total unless the text clearly supports addition.
- Do not add account totals plus suballocations, loan authority plus loan subsidy cost, user fees plus account totals, transfers as new funding, rescissions as positive funding, or set-asides inside a broader amount unless the user specifically asks for that category and the facts support the relationship.
- For mixed financial-type questions, group amounts by type first.
- If arithmetic across mixed types is useful, label it as "Mixed identified total" and state that it combines different financial types and should not be treated as one clean funding pool."""


MODE_EXAMPLES: dict[str, str] = {
    "direct_account_amount": """Direct account example:
Question: What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?
Facts include $6,957,972,000 for FDA Salaries and Expenses, necessary FDA expenses including passenger motor vehicles, space rental and related costs, special-purpose space, and emergency enforcement, program/center activities such as Human Foods, CDER, CBER, CVM, CDRH, NCTR, and Center for Tobacco Products, user fees credited to the account, and a separate nearby $3,000,000 provision.
Good answer pattern: Give the $6,957,972,000 account amount and a compact summary of major allowed uses. Mention that user fees are credited to the account under applicable laws only if useful for clarity. Do not list every center suballocation, do not include the separate nearby $3,000,000 provision, and do not create a "Not added separately" section unless the user asks for a breakdown or reconciliation.""",
    "broad_topic_total": """Broad total example:
Question: how much for FEMA?
Facts include FEMA operations and support $1,483,990,000, FEMA procurement/construction/improvements $99,528,000, FEMA Federal Assistance $3,497,019,369, Disaster Relief Fund $20,261,000,000, National Flood Insurance Fund $239,983,000, and a $33,000,000 transfer to FEMA Federal Assistance.
Good answer pattern: Start with "FEMA total found: $25,581,520,369" when adding those retrieved top-level comparable buckets. Include operations/support, procurement/construction/improvements, Federal Assistance, Disaster Relief Fund, and National Flood Insurance Fund. Do not add the $33,000,000 transfer separately.""",
    "funding_mechanism_no_amount": """Funding mechanism example:
Question: how much money for FEMA?
Facts include that amounts made available by continuing appropriations to the Department of Homeland Security under "Federal Emergency Management Agency--Disaster Relief Fund" may be apportioned up to the rate for operations necessary for Stafford Act response and recovery. Facts also include unrelated Indian Health Service amounts.
Good answer pattern: Say "FEMA total found: no FEMA-specific dollar amount identified in the extracted facts." Then explain that the retrieved text provides funding-mechanism evidence for continuing/apportioning Disaster Relief Fund operations, but no explicit FEMA dollar figure. Omit unrelated Indian Health Service amounts as not responsive.""",
    "reconciliation_breakdown": """Reconciliation example:
Question: how much for FEMA and immigration combined?
Facts include FEMA Federal Assistance $3,497,019,369, ICE operations and support $9,501,542,000, ICE enforcement/detention/removal $5,082,218,000, USCIS operations and support $271,140,000, USCIS Citizenship and Integration grants $10,000,000, and CBP operations and support $18,426,870,000.
Good answer pattern: Start with "FEMA total found", "Immigration-related total found", and "Combined FEMA + immigration-related total found" only when the arithmetic is source-backed. Then use separate FEMA and Immigration-related sections. Do not add the ICE enforcement/detention/removal component separately when the broader ICE operations/support amount is included.""",
    "general_summary": """General summary example:
Question: What does this division do for FDA facilities?
Good answer pattern: Summarize the directly relevant provisions and cite retrieved facts. Include amounts only if they directly explain the answer.""",
}


MIXED_FINANCIAL_TYPE_EXAMPLE = """Mixed financial types example:
Question: What FY2026 funding is available for rural water/wastewater infrastructure?
Facts include USDA Rural Utilities Service direct loan authority $X, USDA Rural Utilities Service guaranteed loan authority $Y, USDA Rural Utilities Service subsidy/grant/program funding $Z, USDA technical assistance/circuit rider funding $A, and EPA targeted grant funding $B.
Good answer pattern: Group the answer by financial type: direct loan authority, guaranteed loan authority, subsidy/grant/program funding, technical assistance, and targeted grants. Do not present X+Y+Z+A+B as a clean grant pool or top-line appropriation. If showing arithmetic across all retrieved figures, label it as "Mixed identified total: $N" and explain that it combines different financial types and should not be treated as one clean funding pool."""


SYNTHESIS_BASE_RULES = """Synthesis rules:
- Write a short top-level summary first.
- Combine already-short division results rather than appending dense sections.
- Do not drop a division; divisions with no direct evidence should appear only as short no-direct-info lines.
- Group broad answers primarily by controlling agency/account, with division labels secondary.
- Preserve relevant dollar figures and citation markers from division answers.
- Preserve existing [[num:...]] markers immediately after their visible source or derived figures.
- If you repeat or restate a marked dollar figure in the answer, by-division section, or caveats, repeat the same [[num:...]] marker immediately after every occurrence of that same figure.
- Do not write a source-backed or derived dollar figure without its existing marker when that figure appears in the division answers with a marker.
- Keep citation markers immediately after the figure or clause they support.
- Do not introduce topic sections that were not requested by the question and are not directly relevant to the division answers.
- Do new accounting only when combining comparable division totals.
- Target 8-12 substantive bullets for broad answers. Exceed that only when more direct responsive accounts truly require it.
- Avoid duplicating caveats across division sections and final caveats.
- Do not repeat the same agency, account, bucket, or dollar figure in both the top Answer and By Agency / Account.
- The top Answer is a summary only; detailed amounts belong in By Agency / Account.
- Use By Agency / Account for broad topic answers, not full By Division restatements.
- Use Not Included for routed divisions with no direct responsive evidence or only adjacent evidence.
- Not Included entries must be one line each.
- Caveats must be 2-3 bullets max unless the user explicitly asks for reconciliation.
- Do not create a Caveats section that restates every Not Included or suballocation note.
- If a caveat belongs to one bucket, put it in that bucket sentence instead of repeating it globally.
- For broad mixed-financial-type answers, preserve all direct controlling accounts/buckets, but compress suballocations under the parent account.
- Target 8-12 substantive bullets total across By Agency / Account and Not Included.
- For any new calculated total, add a new marker like [[num:drv_final_1]] immediately after the visible total and add a matching derived annotation.
- Derived annotation input_ids must reference existing source or derived marker ids from the available annotations.
- Use clear language, clear numbers, and no filler."""


SYNTHESIS_EXAMPLE = """Synthesis example:
For a broad infrastructure question, write one bottom-line paragraph, then group direct responsive buckets by controlling agency/account, such as USDA RUS [AG] and EPA [INT]. Put routed but non-responsive divisions like THUD in Not Included as one-line notes. Use Caveats only for cross-cutting warnings such as mixed financial types; do not repeat each account's hierarchy caveat."""


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


def _mode_reduce_rules(answer_mode: str, flags: dict[str, Any] | None) -> str:
    mode = normalize_answer_mode(answer_mode)
    sections = [
        "Answer-mode instructions:",
        f"- Selected answer_mode: {mode}",
        f"- Active safety flags: {mode_flags_text(flags)}",
        MODE_REDUCE_RULES[mode],
    ]
    if (flags or {}).get("mixed_financial_types"):
        sections.extend([MIXED_FINANCIAL_TYPE_RULES, MIXED_FINANCIAL_TYPE_EXAMPLE])
    sections.append(MODE_EXAMPLES[mode])
    return "\n\n".join(sections)


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
        "- Then answer directly and concisely.\n"
        "- Use an Included / Not added separately structure only when answer-mode instructions call for it or double-counting risk must be made explicit.\n\n"
        f"{INVARIANT_RULES}\n\n"
        f"{_mode_reduce_rules(answer_mode, answer_mode_flags)}\n\n"
        "Responsiveness rules:\n"
        "- Build substantive answer content from Direct facts.\n"
        "- Use Adjacent facts only for short not-included or scope notes unless needed to clarify why they were not counted.\n"
        "- Do not use Not responsive facts in the answer.\n"
        "- If a routed division has no Direct facts, write a short no-direct-info line with the best adjacent reason when available.\n"
        "- For broad answers, group primarily by controlling agency/account, with division labels secondary.\n"
        "- Target 8-12 substantive bullets for broad mixed-topic answers. Exceed that only when more than 12 direct responsive accounts or buckets materially answer the question.\n"
        "- Keep direct suballocations when useful, but group them compactly under the parent account and do not repeat the same caveat elsewhere.\n\n"
        "Reduce compactness rules:\n"
        "- Do not write a long Caveats section at reduce. Put local double-counting or hierarchy notes next to the relevant account/bucket.\n"
        "- For divisions with direct evidence, keep the answer compact enough for synthesis to reuse: controlling account, top-level amount/type, and compact direct suballocations.\n"
        "- For divisions with no direct facts, return only the heading plus one no-direct-info sentence using the best adjacent reason.\n\n"
        "Rules:\n"
        "- Before writing, classify facts internally as DIRECT, SUPPORTING, or IRRELEVANT. Use DIRECT plus only essential SUPPORTING facts in the final answer.\n"
        "- Preserve all relevant dollar figures from the extracted facts.\n"
        "- Preserve existing [[num:...]] markers immediately after their visible source figures.\n"
        "- If you repeat or restate a marked dollar figure in the bottom line, accounts/programs, or notes, repeat the same [[num:...]] marker immediately after every occurrence of that same figure.\n"
        "- Do not write a source-backed dollar figure without its existing marker when that figure appears in the extracted facts with a marker.\n"
        "- Keep citation markers immediately after the figure or clause they support.\n"
        "- Do not invent totals unless the extracted facts explicitly support the arithmetic.\n"
        "- Do not omit relevant accounts or programs just to be concise.\n"
        "- If the facts do not answer the question, say so in the bottom line.\n"
        "- For any calculated total, add a new marker like [[num:drv_dhs_1]] immediately after the visible total and add a matching derived annotation.\n"
        "- Derived annotation input_ids must reference existing source or derived marker ids from the available annotations.\n\n"
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
        "Use this markdown structure:\n"
        "## Answer\n"
        "<1 short paragraph with the bottom line. State whether a clean total is available.>\n\n"
        "## By Agency / Account\n"
        "- **<Agency or account> [ACRONYM]:** <top-level responsive amount(s) and control point. Include compact direct suballocations only when they materially answer the question.>\n"
        "- **<Agency or account> [ACRONYM]:** <same pattern>\n\n"
        "## Not Included\n"
        "- **<Division/acronym>:** <one-line reason when a routed division has no direct responsive funding or only adjacent material.>\n\n"
        "## Caveats\n"
        "- <2-3 bullets max. Only caveats needed to prevent misreading or double counting. Do not repeat caveats already stated beside a bucket.>\n\n"
        f"Selected answer_mode: {normalize_answer_mode(answer_mode)}\n"
        f"Active safety flags: {mode_flags_text(answer_mode_flags)}\n\n"
        f"{INVARIANT_RULES}\n\n"
        f"{SYNTHESIS_BASE_RULES}\n\n"
        f"{SYNTHESIS_EXAMPLE}\n\n"
        f"{MIXED_FINANCIAL_TYPE_RULES if (answer_mode_flags or {}).get('mixed_financial_types') else ''}\n\n"
        f"Question:\n{question}\n\n"
        f"Available annotations:\n{annotation_context}\n\n"
        f"Division answers:\n{division_context}"
    )
