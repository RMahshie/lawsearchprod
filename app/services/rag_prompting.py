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
- Preserve source and citation details exactly where they belong.
- Do not invent facts, dollar figures, or totals.
- Use only retrieved facts.
- Only sum comparable additive amounts in the same scope.
- Preserve caveats for transfers, rescissions, caps, fees, set-asides, suballocations, limitations, and non-comparable accounts.
- Do not substitute unrelated dollar figures when the requested topic lacks a dollar amount.
- Distinguish funding-mechanism evidence from dollar-figure evidence."""


FIGURE_HANDLE_RULES = """Figure Handle contract:
- Evidence dollar figures appear as self-describing atomic handles such as {{F1:$25,000}}. The amount is part of the handle. To use or repeat that figure, copy the whole exact handle. Do not type the dollar figure separately.
- Never output canonical [[num:...]] markers. The backend owns canonical marker rendering.
- Never invent or alter an {{F#:$...}} handle. Use only exact whole handles present in the supplied evidence.
- For a calculated figure, put a new handle such as {{D1}} in `answer` and add exactly one matching `derived_annotations` item with id `D1`.
- A Derived Figure's input_ids must contain existing local handles such as `F1`, `F2`, or an earlier `D1`, without braces.
- Do not put any raw dollar figure outside a handle in `answer`. Every visible amount must be represented by an available {{F#:$...}} handle or a matching proposed {{D#}} handle."""


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


MAP_MODE_PROMPTS: dict[str, str] = {
    "direct_account_amount": """Mode-specific map rules (direct_account_amount):
- Direct: facts about the named account, program, or agency in the question.
- Treat each clause of the question as part of the Direct scope. If the question asks for plural amounts, tranches, availability dates, or funding changes, Direct includes every named-account current, advance, or prior tranche that is relevant to the requested fiscal year, plus its availability period, reimbursements, transfers, and rescissions.
- A rescission from an earlier named-account tranche is Direct when the question asks which amounts are identified or how those amounts are available. Preserve it as a rescission, not positive funding.
- When a service or activity list is funded across the named account and sibling accounts, keep the list Direct if it answers the requested uses, but preserve the pooled multi-account scope explicitly.
- Adjacent: nearby provisions in the same section or title that are not the named account, and sibling accounts under the same parent agency that are not the requested one.
- Not_responsive: unrelated accounts, unrelated suballocations, center-by-center figures, individual user-fee line amounts, and rent/transfer/limitation line items, unless the question asks for breakdown or reconciliation.
- Do not promote nearby provisions to direct merely because they appear in the same chunk.
- Preserve the named account's main appropriation amount and any allowed-use language as direct facts.""",
    "broad_topic_total": """Mode-specific map rules (broad_topic_total):
- Direct: any fact that provides or controls funding for the same project type as the question, a closely related project type, or a relevant eligible population or geography, even when the chunk does not repeat the user's exact phrase.
- Direct includes top-level funding lanes for the topic: appropriated grants, assistance payments, benefit payments, direct loan authority, guaranteed loan authority, loan subsidy costs, dedicated program accounts, trust-fund accounts, major set-asides, and topic-specific fee or collection authorities.
- When the question names multiple topics or project types, evaluate each named topic independently and preserve direct facts for each one before broader related facts.
- Treat account, program, authority, eligible-activity, eligible-population, or geography language as direct when it substantively matches the user's requested topic, even if the bill text uses different wording than the question.
- Treat statutory authority references, public-law references, and account headings as direct when they are the bill text's concrete label for the requested topic or a named subtopic.
- If a retrieved chunk begins mid-sentence, still extract visible amount or authority clauses when their account heading, statutory section, or surrounding text clearly matches the requested topic; do not discard them solely because preceding sentence context is missing.
- If a chunk is a continued account heading, continued statutory title, or continued enumerated list, extract each visible item that matches a user-stated topic even when the parent heading or lead-in phrase is in an adjacent Chunk. Preserve any visible item number, section label, or parent-child language instead of treating the item as unrelated.
- Direct facts may be dollar-free mechanism facts when they authorize, collect, obligate, extend, limit, or otherwise control funding for the requested topic.
- Preserve exact statutory section labels, public-law references, account headings, and named authorities for direct facts when they appear in the source text.
- Adjacent: tiny caps, administrative-expense limitations, transfers, rescissions, and small carveouts inside a broader account when stronger funding lanes for the topic are also present in the chunk.
- Adjacent: facts that mention the topic only in passing or as one of many eligible uses without a topic-specific amount or authority.
- Promote a cap, administrative-expense limit, transfer, rescission, or small carveout to direct only when no stronger funding lane for the topic appears in the same chunk.
- Not_responsive: unrelated agency or program funding that does not support the topic, related project types, related populations, or related geographies.
- Do not classify a fact as not_responsive solely because it lacks the user's exact phrase; if it funds the same project type or eligible population, it is direct or adjacent.""",
    "funding_mechanism_no_amount": """Mode-specific map rules (funding_mechanism_no_amount):
- Direct: continuing-appropriations, rate-for-operations, apportionment-authority, extension, and referenced-prior-law language that controls funding for the requested topic. Extract these as facts even when no dollar figure is present, with no source_numbers item.
- Direct: explicit references to a prior law, account, or fund that the requested topic's funding flows through.
- Adjacent: mechanism language for related-but-not-requested programs in the same source bucket.
- Not_responsive: unrelated dollar figures from the same division or source bucket. Do not extract them as substitutes for a missing topic-specific amount.
- Do not invent or infer a dollar figure from mechanism language; preserve the mechanism as a fact and leave the amount unspecified.""",
    "reconciliation_breakdown": """Mode-specific map rules (reconciliation_breakdown):
- Direct (within the requested scope): parent account totals, child allocations and suballocations, financing sources such as user fees and offsetting collections, transfers in and out, caps, limitations, rescissions, set-asides, and exclusions needed to audit the math.
- Preserve parent-child relationship language on every fact: 'of which', 'to remain available', 'derived from fees', 'transferred', 'rescinded', 'not to exceed', 'loan authority'.
- Preserve the financial-type label on each amount (account total, suballocation, grant, direct loan authority, guaranteed loan authority, loan subsidy cost, user fee, offsetting collection, transfer, rescission, set-aside, cap, limitation) so the reduce stage can classify additive relationships.
- Adjacent: related accounting context inside the same account that does not bear on the requested reconciliation math.
- Not_responsive: amounts outside the requested topic or account scope.
- Be exhaustive within scope; do not collapse multiple suballocations into a single fact.""",
    "general_summary": """Mode-specific map rules (general_summary):
- Direct: facts that directly answer the user's non-numeric or lightly numeric question.
- For summary questions, extract the provision's purpose, authority, restriction, prohibition, reporting or oversight requirement, eligible activity, program family, financing/source-support mechanism, or operational effect as the direct fact. Classify dollar figures as adjacent unless the question specifically asks about amounts or the amount is essential to explain the provision.
- Treat non-dollar governance facts as direct when they materially explain what the division, account, program, or continuing mechanism does; do not demote them merely because they lack a dollar figure.
- When the question names a specific agency, account, program, or entity, Direct facts must materially involve that named target or a division-wide governance requirement that clearly applies to that target. Other agencies or programs in the same Division are adjacent or not_responsive, not Direct.
- When a chunk lists related categories, accounts, user-fee sources, activities, project types, or eligible uses, extract the category list as a compact direct summary fact instead of one amount-by-amount ledger.
- When the question asks what a division or account does, prefer breadth across distinct agencies, accounts, program families, activities, restrictions, and oversight requirements over repeated dollar lines from one account.
- Adjacent: contextual provisions that help frame the answer but are not the answer itself.
- Not_responsive: unrelated provisions retrieved alongside the relevant text.
- Do not turn a summary question into a ledger; prefer one fact per substantive provision and omit nonessential figures from direct facts.""",
}


MAP_EXAMPLE = """Map example:
Question: What amount is appropriated for a named account?
Relevant chunk text says the named account receives a main appropriation and a nearby section provides a separate amount for a different purpose.
Good fact object: responsiveness_tier=direct, fact="- The named account is appropriated the main account amount for necessary expenses. [ACR]"
The separate nearby amount should be adjacent or not_responsive unless it directly answers the question."""


REDUCE_MODE_PROMPTS: dict[str, str] = {
    "direct_account_amount": """Direct account reduce prompt:
- Use only Direct facts to answer. Use Adjacent facts only for one short scope note when necessary. Do not use Not responsive facts in the answer.
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Do not invent facts, dollar figures, or totals. If the facts do not answer the question, say that directly.
- Answer the specific account/program question directly and compactly.
- Default shape: main amount first, then 1 short paragraph. When summarizing multiple major allowed-use categories, use a short bullet list for readability.
- Identify the account, give the main appropriation amount, and summarize major allowed uses when asked.
- Answer every requested component. When the question asks for multiple amounts, tranches, availability dates, reimbursements, transfers, or rescissions, enumerate the relevant account-level Direct facts and label their relationships; do not collapse them to one headline amount.
- Coverage priority is mandatory: first include every Direct account-level fact that answers an explicit amount, tranche, availability-date, reimbursement, transfer, or rescission clause; then summarize requested uses or services. Do not spend answer space on internal suballocation figures before those account-level facts are covered.
- Do not substitute a different same-agency account amount for a requested named-account tranche.
- If a retrieved service or activity list is pooled across the named account and sibling accounts, say so instead of attributing the whole list solely to the named account.
- For "major allowed uses", summarize categories of use; do not list every center, activity, rent line, transfer, limitation, or user-fee amount unless the user asks for a detailed allocation, breakdown, or reconciliation.
- For "major allowed uses", name categories only. Do not attach dollar figures to internal centers, activities, rent lines, or other suballocations unless the user asks for allocation, breakdown, line items, or "how much for each".
- When the user asks what kinds of care, services, or activities are covered, state the category names without their internal set-aside amounts unless those amounts were also explicitly requested.
- Separate internally: main appropriation amount, suballocations within that amount, user fees credited to the account, separate provisions outside the account, and limitations/transfers.
- Surface only categories needed to answer the user.
- Mention user fees as credited to the account only when useful for clarity; do not list each user-fee dollar amount unless the user asks for user fees or a funding-source breakdown.
- Do not create Included / Not added separately sections unless the user asks for reconciliation/breakdown or excluding a specific amount is necessary to prevent likely double counting.
- Prefer one concise caveat sentence over a ledger-style excluded-amount section.
- Do not include nearby provisions merely because they were retrieved.
- If you repeat or restate an evidence dollar figure, repeat the same Figure Handle for every occurrence.
- For any calculated total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.

Direct account example:
Question: What amount is appropriated for a named account in FY2026, and what are the major allowed uses?
Facts include the main account appropriation, necessary-expense language, activity categories, user fees credited to the account, and a separate nearby provision.
Good answer pattern: Give the main account amount, then write "Major allowed uses include:" followed by category-only bullets. Mention that user fees are credited to the account under applicable laws only if useful for clarity. Do not list every internal activity suballocation, do not include activity-by-activity dollar figures, do not list individual user-fee dollar figures, do not include separate nearby provisions, and do not create a "Not added separately" section unless the user asks for a breakdown or reconciliation.
Bad answer pattern: listing every internal activity amount unless the user asks for allocations.
Bad answer pattern: listing each individual fee-source amount unless the user asks for a user-fee breakdown.""",
    "broad_topic_total": """Broad topic total reduce prompt:
- Use only Direct facts for substantive answer content. Use Adjacent facts only for short not-included or scope notes. Do not use Not responsive facts in the answer.
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Do not invent facts, dollar figures, or totals. If the facts do not answer the question, say that directly.
- Output a compact division brief for synthesis, not a full ledger.
- Default shape for divisions with direct evidence: Bottom line: <1 sentence naming the controlling agency/account(s) and whether a clean total is available>; Key buckets: <3-6 compact bullets when needed, grouped by controlling agency/account/program>; Local caveat: <optional 1 sentence only if needed to prevent double counting>.
- Use one bullet per controlling account/program. Do not create separate bullets for suballocations within the same parent account.
- Include top-level amounts and decision-useful sub-buckets. Omit unrelated internal earmarks, administrative amounts, and repeated duplicate figures unless the user asks for detail, but keep smaller suballocations when they directly match a named user topic or explain a primary funding lane.
- Do not omit a retrieved controlling parent account, major formula/block grant, or primary assistance lane in favor of narrower set-asides from the same topic.
- When the question explicitly names several topics, include the direct facts for those named topics before broader account totals. Do not omit a direct named-topic amount or dollar-free fee authority merely to keep the brief shorter.
- Before finalizing, check the user-stated topics against the Direct facts. If Direct facts exist for a named topic, include at least one bucket or nested sub-bucket for that topic unless it would duplicate the same parent amount.
- When a direct fact contains a parent amount and an in-scope child/suballocation amount, preserve both in the same bucket and label the child relationship.
- When Direct facts include a controlling parent account plus named-topic child allocations, preserve the parent account and the named-topic child allocations in the same bucket; compact the wording instead of dropping the children.
- When several Direct facts belong to the same controlling account, nest them under that account rather than moving them into separate thematic buckets.
- Preserve exact statutory section labels, public-law references, account headings, and named authorities for direct facts when they appear in the source text.
- Provide a "total found" only when top-level comparable additive buckets are present in the same scope.
- Do not compute or lead with a mixed identified total unless the user explicitly asks for a summed identified amount.
- If figures mix financial types or hierarchy is unclear, lead with grouped buckets instead of one clean headline total.
- Before aggregating, classify each amount internally by financial type and additive relationship: account total, suballocation, grant, direct loan authority, guaranteed loan authority, loan subsidy cost, user fee, offsetting collection, transfer, rescission, set-aside, cap, or limitation.
- Do not add account totals plus suballocations, loan authority plus loan subsidy cost, user fees plus account totals, transfers as new funding, rescissions as positive funding, or set-asides inside a broader amount unless the user specifically asks for that category and the facts support the relationship.
- For routed divisions with no Direct facts, return only the heading plus one no-direct-info sentence using the best Adjacent reason.
- When the question names multiple topics, preserve at least one decision-useful bucket for each named topic when Direct facts exist.
- If you repeat or restate an evidence dollar figure, repeat the same Figure Handle for every occurrence.
- For any calculated comparable total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.

Broad total example:
Question: how much for a named agency?
Facts include several top-level agency accounts and a transfer into one of those accounts.
Good answer pattern: Start with a total found only when adding retrieved top-level comparable buckets. Include the top-level accounts. Do not add the transfer separately when it moves money into an already-included account.

Mixed financial types example:
Question: What FY2026 funding is available for a broad infrastructure topic?
Facts include one controlling program account with direct loan authority, guaranteed loan authority, subsidy/grant funding, and targeted assistance or grant buckets.
Good answer pattern: Use one controlling account/program bullet that names the comparable and non-comparable financial types separately. Mention key assistance or grant buckets compactly only if they materially help the user locate the funding. Do not split every minor set-aside into separate bullets. Do not present loan authority plus grants or subsidy costs as one clean total.""",
    "funding_mechanism_no_amount": """Funding mechanism reduce prompt:
- Use only Direct facts to answer. Use Adjacent facts only for one short scope note when necessary. Do not use Not responsive facts in the answer.
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Do not invent facts, dollar figures, or totals.
- Distinguish dollar-figure evidence from funding-mechanism evidence.
- Continuing appropriations, rate-for-operations language, apportionment authority, extensions, and referenced prior laws can explain how funding continues, but they are not dollar amounts.
- If the requested topic has funding-mechanism evidence but no relevant dollar figure, say that a dollar total was not found in the extracted facts and explain what mechanism was found.
- If answering the dollar amount requires a prior-year baseline or referenced law that is not present in the extracted facts, say that explicitly.
- For continuing-resolution questions about what happens without a full-year appropriation, state that the rate, authority, and conditions come from the applicable fiscal year 2025 appropriations Acts when that fact is retrieved.
- Include retrieved payment/obligation categories that explain what can continue, such as personnel pay and benefits, mandatory payments, essential activities to protect life and property, and orderly termination of government functions.
- Do not substitute unrelated dollar figures from the same division or source bucket.
- Do not create Included / Not added separately sections, totals, or reconciliation tables.
- Keep the response compact: one bottom-line sentence plus up to 3 mechanism bullets when useful.
- If you repeat or restate an evidence dollar figure, repeat the same Figure Handle for every occurrence.
- For any calculated total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.

Funding mechanism example:
Question: how much money for a named agency under a continuing appropriation?
Facts include that amounts made available by continuing appropriations to the department under a named agency account may be apportioned up to the rate for operations for specified statutory purposes. Facts also include unrelated amounts for another agency.
Good answer pattern: Say that no agency-specific dollar amount was identified in the available bill text. Then explain that the retrieved text provides funding-mechanism evidence for continuing or apportioning the named account, but no explicit dollar figure. Omit unrelated agency amounts as not responsive.""",
    "reconciliation_breakdown": """Reconciliation and breakdown reduce prompt:
Use this markdown structure. Only include subsections that apply:

### [ACRONYM] <Division>

Bottom line: <account total / reconciliation summary>

## Included
### Programmatic breakdown
- <account/activity>: <amount>
- <account/activity>: <amount>

### Financing-source breakdown
- <user-fee/source>: <amount>
- <user-fee/source>: <amount>

## Not Added Separately
### Suballocations within included amounts
- <amount>: <why not added>

### Transfers, caps, and limitations
- <amount>: <why not added>

### Financing-source treatment
- <amount/category>: <why not added>

## Caveats
- <only if needed>

- Use Direct facts for substantive answer content. Use Adjacent facts only for short not-included or scope notes. Do not use Not responsive facts in the answer.
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Do not invent facts, dollar figures, or totals. If the facts do not answer the question, say that directly.
- Do not use internal pipeline language in the answer, including "extracted facts", "provided facts", "retrieved facts", "mapped facts", "division answers", or "source chunks".
- Use user-facing language such as "the identified provisions", "the account text", "the bill text", or "the available FY2026 text".
- When explaining uncertainty, do not say the extracted facts do not resolve it. Say what the bill text or identified provisions do and do not establish.
- Use the markdown structure above when the user asks for a breakdown, combined total, reconciliation, show math, included/excluded amounts, double-counting analysis, comparison, or multiple named topics.
- Keep Included for amounts that directly answer the requested breakdown. Keep Not Added Separately for figures that explain accounting boundaries, double counting, or why a nearby amount is excluded.
- For topical breakdowns, do not put a broad parent account total in Included as if the whole account is the requested topic unless the Direct facts establish that all of the parent account is in scope. If the parent account contains both in-scope and out-of-scope items, use it as context or place it in Not Added Separately with that caveat.
- Do not present a topical subtotal unless every component in the subtotal is listed, source-backed, same-scope, and comparable. If those components are incomplete or include nested child amounts, say no clean subtotal is established.
- For combined-topic questions, provide one total found per topic and a combined total found only when those topic totals are clearly additive.
- Preserve enough detail to audit the math.
- If a broader parent account and one of its components both appear, include the parent account and explain that the component was not added separately.
- Before finalizing the Included section, scan every Included amount for relationship language such as "within", "of which", "of the total", "from amounts made available", "reserved", "set aside", "not less than", "not to exceed", "for such grants", or "for this purpose". If an amount is a subset, reservation, cap, transfer, fee source, or component of another Included amount, move it to Not Added Separately and explain the parent-child relationship.
- Never place the same child/suballocation amount in Included and Not Added Separately. Use Not Added Separately for the child when the parent is Included.
- Moving a child amount to Not Added Separately does not mean omitting it. For reconciliation questions, enumerate all retrieved in-scope child allocations and suballocations needed to audit the account, including lines nested under a parent amount.
- When the question asks to break down an account or category "including" named subcategories, preserve every retrieved in-scope line item for those categories. Do not compress a list of grant, capitalization, project, activity, fee-source, or limitation lines into only the parent total.
- If the requested breakdown covers one topic within a broader account that also has out-of-scope items, state the broader account total as context or Not Added Separately and then enumerate the retrieved in-scope component lines under the requested topic.
- Keep sibling parent lines distinct when the source distinguishes them, such as separate funds, accounts, grant programs, fee sources, or capitalization grants. Do not relabel one sibling's amount as the generic parent for all siblings.
- When the user asks for a grouped category and same-type child figures are retrieved, state simple same-type subtotals without mixing financial types.
- Group breakdown bullets under their topic, account, or financial relationship instead of writing one flat accounts list.
- For account breakdown questions, separate programmatic/activity allocations from financing-source or fee-source amounts when both appear.
- Classify excluded amounts by relationship: suballocation, transfer, fee/offset, cap/limitation, rescission, administrative amount, component, or unknown.
- Put excluded transfer, cap, administrative amount, component, or related figure under the relevant topic's Not added separately subsection rather than creating a new topic section.
- Do not add account totals plus suballocations, loan authority plus loan subsidy cost, user fees plus account totals, transfers as new funding, rescissions as positive funding, or set-asides inside a broader amount unless the user specifically asks for that category and the facts support the relationship.
- If figures are mixed but the user asked for reconciliation, preserve the math and label any cross-type arithmetic as a mixed identified total, not a clean funding pool.
- If you repeat or restate an evidence dollar figure, repeat the same Figure Handle for every occurrence.
- For any calculated total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.

Parent-total validation:
- When same-scope child allocations sum to a Source-backed Figure parent account total, you may add a separate "reconciles to" line using a new Derived Figure Handle and a matching derived annotation whose input_ids reference the child handles.
- Place the new Derived Figure Handle on its own reconciliation line. Do not reuse the parent's Source-backed Figure Handle for the calculated validation line.
- Label this as "reconciles to the account total" or "validation check", not as a new appropriation or funding pool.
- Use this only when the math actually works (same financial type, same scope, children sum to parent). Do not force a reconciliation when figures do not sum cleanly. Do not extend this carve-out to mixed financial types.

Reconciliation example:
Question: how much for two named topics combined?
Facts include one top-level account for the first topic, several top-level accounts for the second topic, and child components nested within one of the top-level accounts.
Good answer pattern: Start with one total found per topic and a combined topic total found only when the arithmetic is source-backed. Then use separate sections for each topic. Do not add a child component separately when the broader parent account is included.""",
    "general_summary": """General summary reduce prompt:
- Use only Direct facts for substantive answer content. Use Adjacent facts only for one short scope note when necessary. Do not use Not responsive facts in the answer.
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Do not invent facts, dollar figures, or totals. If the facts do not answer the question, say that directly.
- Do not use internal pipeline language in the answer, including "extracted facts", "provided facts", "retrieved facts", "mapped facts", "division answers", or "source chunks".
- Answer the user's question directly using the retrieved facts.
- Keep the answer concise and explanatory. Use short paragraphs for narrow summaries; use 4-7 compact bullets when the Direct facts cover several distinct agencies, accounts, program families, activities, restrictions, or oversight requirements.
- Include dollar figures only when they directly explain the answer.
- When the user asks for a plain-English summary or says not to do a detailed dollar breakdown, omit most dollar figures. Mention only the few figures needed to explain scale or a controlling provision.
- When the user explicitly asks not to do a detailed breakdown, do not include named program dollar figures inside category lists; use account, program, financing, authority, and activity names instead.
- If the user says not to do a detailed dollar breakdown, do not list program-by-program amounts, loan authorities, grant amounts, or authorization changes. Use category names instead, with at most one or two figures only if essential.
- Before compressing, preserve every material coverage category supported by Direct facts: funding/account purpose; major program or activity families; financing or fee-support mechanisms; authorities or eligibility rules; restrictions or prohibitions; reporting, planning, oversight, or notification requirements; and temporary/continuing mechanism terms.
- Do not let dollar-bearing facts crowd out dollar-free Direct facts such as restrictions, prohibitions, reporting obligations, prior-law authority, conditions, or eligibility rules.
- Plain-English summaries should still mention how the work is supported or controlled when Direct facts show it: user fees, offsetting collections, transfers, continuing authority, obligation plans, reporting deadlines, committee notifications, and oversight requirements. Suppress nonessential figures, not these mechanisms or obligations.
- When Direct facts include a category list, keep the category names in compact prose and omit the individual dollar amounts unless they are essential to the user's question.
- Do not replace a retrieved category list with vague wording such as "various", "multiple", "several", or "user-fee accounts" when the category names materially answer the question.
- When the question names an agency, account, or program, preserve the formal account/program heading from Direct facts at least once when it explains the funding or authority. Do not paraphrase a formal account heading into only generic words like "core operations".
- For named-entity summaries, keep compact named lists of financing/support categories from Direct facts, such as user-fee categories, eligible activity families, or regulatory/oversight lanes. The list can be prose, but it must not collapse named categories into "multiple sources" or "various activities".
- Preserve financing-mechanism nouns such as loans, loan guarantees, grants, subsidies, technical assistance, fees, capitalization grants, transfers, and authorization changes when they explain what support is available; suppress the figures, not the mechanism.
- For division-wide coverage questions, keep distinct program families, bureaus, administrations, facility programs, regulatory programs, cleanup programs, emergency programs, and oversight programs as named categories when Direct facts support them.
- Preserve concrete deadlines, timeframes, named recipients, and statutory conditions from Direct reporting, planning, notification, restriction, or prohibition facts when those details define the obligation.
- For division-wide coverage questions, name each major retrieved agency, bureau, commission, account family, or program family at least once instead of collapsing them into generic division-level language.
- For coverage questions asking what a Division covers, supports, or does, convert account totals, obligation limits, grant amounts, loan authorities, and set-asides into program-category language unless the user asked how much or the amount itself defines the mechanism.
- When Direct facts support broad category families and narrower implementation details, preserve the broad family names first: infrastructure modes, assistance families, housing/rental/homelessness/supportive-housing lanes, oversight/reporting lanes, and restriction/eligibility lanes.
- For continuing-appropriations summaries, state when supported that continuing appropriations preserve prior-law authority, conditions, or manner of operation, and distinguish them from new full-year line-item appropriations.
- For compare/contrast questions, explicitly state each retrieved side of the contrast and the practical difference between them.
- Do not turn a non-numeric question into a reconciliation ledger.
- Do not create Included / Not added separately sections unless the user explicitly asks for accounting.
- If you repeat or restate an evidence dollar figure, repeat the same Figure Handle for every occurrence.
- For any calculated total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.

General summary example:
Question: What does this division do for a named agency's facilities?
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
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Keep the final answer compact: main amount first, then 1-2 short paragraphs or up to 4 bullets for requested uses/context.
- Preserve all distinct account-level tranches, availability dates, reimbursements, transfers, and rescissions when the question explicitly asks for them; do not reduce plural amounts to one headline amount.
- Preserve any stated pooled multi-account scope for service or activity lists.
- Do not introduce By Agency / Account, Included, or Not added separately sections.
- Do not list every suballocation, center, activity, rent line, transfer, limitation, or user-fee amount unless the user asked for that detailed breakdown.
- If more than one division has competing direct answers, say that clearly instead of merging them.
- Routed divisions with no direct evidence should appear only as one-line Source Scope notes.
- For any calculated total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.""",
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
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Do not mention "division answers", "extracted facts", "retrieved facts", "provided facts", or other pipeline/internal process language in the final answer.
- Use these section titles exactly when applicable: "Topic-Specific or Targeted Funding", "Broader Related Funding", "Identified But Not Cleanly Topic-Specific", "Not Included", and "Caveats".
- Do not generate long topic-expanded section names like "Rural Water or Wastewater-Specific or Rural Water or Wastewater-Targeted Funding".
- For broad mixed-financial-type questions, organize by specificity before account detail: topic-specific or targeted funding; broader related funding that may support relevant projects; identified but not cleanly topic-specific; not included.
- Only include sections that have content.
- Do not append full division answers. Combine already-shaped division results.
- Do not create multiple top-level bullets or headings for the same agency/account/heading. Use one heading per controlling account and nest financial types, suballocations, and set-asides underneath it.
- Preserve direct subamounts that help the user identify funding sources, but nest them under the controlling account instead of making them separate top-level accounts.
- When a division answer contains Direct facts for multiple user-stated topics, make a coverage pass before finalizing and keep one bucket or nested line for each named topic that has evidence.
- Use valid markdown bullets for all account details and nested amounts. Indent nested bullets by two spaces.
- Label each amount by financial type where possible: appropriated cost/grant/subsidy, direct loan authority, guaranteed loan authority, grant reservation, administrative expenses, suballocation/set-aside, transfer, cap/limitation, rescission, or user fee.
- Do not repeat the same agency, account, bucket, or dollar figure in both the top Answer and the detailed sections.
- When the question names multiple topics, preserve at least one decision-useful bucket for each named topic when the division answers contain evidence for it.
- Preserve retrieved parent accounts and major formula/block grants before narrower set-asides; do not let many small direct facts crowd out the primary funding lane.
- For broad-topic synthesis, do not drop direct named-topic facts from the division answer in favor of broader account totals. If needed, combine them under the same controlling account bullet.
- Preserve exact statutory section labels, public-law references, account headings, and named authorities for direct facts; include dollar-free authorities when they are directly responsive.
- Do not drop a routed division; if it has no direct evidence, put it in Not Included as one line.
- Provide a clean total only when amounts are comparable and additive in the same scope.
- Do not compute or lead with a mixed identified total unless the user explicitly asks for a summed identified amount.
- Do not add account totals plus suballocations, loan authority plus loan subsidy cost, user fees plus account totals, transfers as new funding, rescissions as positive funding, or set-asides inside a broader amount unless the user specifically asks for that category and the facts support the relationship.
- Caveats must be cross-cutting only. Put local hierarchy or double-counting notes beside the relevant account.
- For any calculated total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.

Good pattern:
### Agency Program Office — Controlling Program Account [ACR]
- Appropriated cost/grant/subsidy: $X
- Loan authority:
  - Direct loans: $Y
  - Guaranteed loans: $Z
- Key identified suballocations within/under this account:
  - Major in-scope set-aside: $A
  - Technical or administrative assistance: $B

Bad pattern:
- Agency Program Office — same account/heading [ACR]: ...
- Agency Program Office — one nested set-aside [ACR]: ...
- Agency Program Office — another nested assistance line [ACR]: ...""",
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
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Do not include unrelated dollar figures from routed divisions.
- Do not create totals, Included sections, Not added separately sections, or reconciliation tables.
- If no direct dollar figure exists, say that no explicit dollar amount was found in the retrieved facts.
- Explain the funding mechanism found, such as continuing appropriation, rate-for-operations, apportionment authority, extension, or referenced prior law.
- If a prior-year baseline or referenced law is required to calculate a dollar amount, say that explicitly.
- For continuing-resolution questions about what happens without a full-year appropriation, state that the rate, authority, and conditions come from the applicable fiscal year 2025 appropriations Acts when that fact is in the division answer.
- Include retrieved payment/obligation categories that explain what can continue, such as personnel pay and benefits, mandatory payments, essential activities to protect life and property, and orderly termination of government functions.
- Routed divisions with no direct evidence should be omitted unless needed as a one-line missing-scope note.
- For any calculated total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.""",
    "reconciliation_breakdown": """Reconciliation synthesis prompt:
Use this markdown structure. Only include subsections that apply:
## Answer
<totals found and combined total only if supported>

## Included
### <topic/account> [ACRONYM]
- <programmatic/activity, financing-source, or financial-type line>: <amount and why included>

## Not Added Separately
### <topic/account or exclusion reason> [ACRONYM]
- <amount/category>: <why not added>

## Caveats
- <math, comparability, or hierarchy caveats needed to audit the answer>

Rules:
- Use only the division answers. Do not invent facts, dollar figures, or totals.
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Do not use internal pipeline language in the answer, including "extracted facts", "provided facts", "retrieved facts", "mapped facts", "division answers", or "source chunks".
- Use user-facing language such as "the identified provisions", "the account text", "the bill text", or "the available FY2026 text".
- When explaining uncertainty, say what the bill text or identified provisions do and do not establish.
- Preserve enough detail to audit the math.
- Preserve each division/account reconciliation structure unless combining comparable topics is explicitly requested.
- Keep Included for amounts that directly answer the requested breakdown. Keep Not Added Separately for figures that explain accounting boundaries, double counting, or why a nearby amount is excluded.
- For topical breakdowns, do not move a broad parent account total into Included as if the entire parent account is the requested topic unless the division answer says all of that account is in scope. If the parent account contains both in-scope and out-of-scope items, mention it as context or keep it in Not Added Separately.
- A clean topical subtotal must be either source-backed or explicitly derived from listed source-backed components that are same-scope and comparable. Do not show a bottom-line topical subtotal from a parent account total plus selected child lines.
- Show combined totals only when topic totals are clearly additive.
- If multiple divisions contain reconciliation results, group by account/topic first, then division only as a secondary label.
- For account breakdown questions, preserve the reduce-stage separation between programmatic/activity allocations and financing-source or fee-source amounts when both appear.
- Identify parent totals, suballocations, transfers, fees/offsets, caps/limitations, rescissions, administrative amounts, and unknown relationships.
- Preserve Included / Not Added Separately distinctions from reduce. Do not move excluded amounts into Included.
- Preserve in-scope child/suballocation lines in Not Added Separately when the reduce answer includes them; do not drop them merely because they are excluded from addition.
- When the user asks for a breakdown "including" named subcategories, preserve the retrieved line items for those categories from the reduce answer. Keep parent/context totals separate from child lines instead of shortening the answer to only the parent total.
- Keep sibling parent lines distinct when the reduce answer distinguishes them, such as separate funds, accounts, grant programs, fee sources, or capitalization grants. Do not turn one sibling amount into a generic parent line for all siblings.
- Preserve same-type subtotals from reduce when they answer requested grouped categories.
- Do not flatten a structured reduce answer into dense paragraphs. Keep the account/topic headings and concise bullets when the reduce answer already has them.
- Do not add account totals plus suballocations, loan authority plus loan subsidy cost, user fees plus account totals, transfers as new funding, rescissions as positive funding, or set-asides inside a broader amount unless the user specifically asks for that category and the facts support the relationship.
- If cross-type arithmetic is retained for user visibility, label it as a mixed identified total, not a clean funding pool.
- Group excluded caveats under the related topic instead of creating unrelated sections.
- For any calculated total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.""",
    "general_summary": """General summary synthesis prompt:
Use this markdown structure:
## Answer
<concise prose or short bullets>

Rules:
- Use only the division answers. Do not invent facts, dollar figures, or totals.
- Preserve source citation markers and copy Figure Handles exactly where their figures belong.
- Answer the user's question directly and concisely.
- Do not force accounting sections.
- Include dollar figures only when they directly explain the answer.
- When the user asks for a plain-English summary or says not to do a detailed dollar breakdown, omit most dollar figures. Mention only the few figures needed to explain scale or a controlling provision.
- When the user explicitly asks not to do a detailed breakdown, suppress program-by-program dollar figures from Division answers and keep the category, mechanism, agency, account, or activity names instead.
- If the user says not to do a detailed dollar breakdown, do not list program-by-program amounts, loan authorities, grant amounts, or authorization changes. Use category names instead, with at most one or two figures only if essential.
- Preserve major coverage categories from each Division answer before compressing: program families, eligible activities, financing/support mechanisms, authorities, restrictions, and oversight/reporting requirements.
- Do not drop a retrieved Division, agency, program family, restriction, or mechanism merely to keep the answer brief; combine related facts into compact category language instead.
- Plain-English summaries should still preserve mechanisms and obligations that explain how the division controls the work, including user-fee support, offsetting collections, transfers, obligation plans, reporting deadlines, committee notifications, and oversight requirements. Omit nonessential figures rather than dropping those categories.
- For named-entity summaries, preserve the formal account/program heading and compact named support categories from the Division answer when they materially answer the question. Do not replace "Salaries and Expenses", named user-fee categories, eligible activity families, or oversight lanes with only generic prose.
- Preserve financing-mechanism nouns from the Division answers, such as loans, loan guarantees, grants, subsidies, technical assistance, fees, capitalization grants, transfers, and authorization changes, while omitting nonessential figures.
- For division-wide coverage questions, keep distinct program families, bureaus, administrations, facility programs, regulatory programs, cleanup programs, emergency programs, and oversight programs as named categories when the Division answers support them.
- Preserve concrete category names, deadlines, timeframes, named recipients, and statutory conditions from the Division answers when those details materially answer the question.
- For multi-Division summary questions, include the distinct role of each routed Division when that Division has Direct evidence.
- For coverage questions asking what a Division covers, supports, or does, prefer category names over visible dollar figures unless the amount is essential to explain the answer.
- When a Division answer includes both broad category families and narrow implementation details, keep the broad family names in the final answer before compressing examples.
- For continuing-appropriations summaries, preserve prior-law authority/conditions language and explicitly distinguish temporary continuing appropriations from new full-year line-item appropriations when the Division answer supports that contrast.
- For compare/contrast summaries, explicitly state the retrieved contrast and practical difference between the mechanisms.
- Do not turn a summary question into a reconciliation ledger.
- Routed divisions with no direct evidence should appear only as one-line scope notes when useful.
- For any calculated total, use a new Derived Figure Handle and a matching derived annotation whose input_ids reference existing local handles.""",
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
    mode = normalize_answer_mode(answer_mode)
    mode_block = MAP_MODE_PROMPTS[mode]
    return (
        "You are a legislative financial analyst extracting evidence from one source chunk.\n\n"
        "Return structured output with `facts`, where each fact has `fact`, `responsiveness_tier`, `reason`, "
        "and `source_numbers` for the dollar figures used in that fact. Legacy `extracted_facts` may be used only "
        "when fact-level objects are unavailable.\n\n"
        "Use this markdown bullet format in extracted_facts:\n"
        "- <specific fact with exact dollar figure/account/program/agency/fiscal year if present> "
        f"[{division_acronym}]\n\n"
        f"Selected answer_mode: {mode}\n"
        f"Active safety flags: {mode_flags_text(answer_mode_flags)}\n\n"
        f"{INVARIANT_RULES}\n\n"
        f"{MAP_BASE_RULES}\n\n"
        f"{mode_block}\n\n"
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
        f"{FIGURE_HANDLE_RULES}\n\n"
        "Answer shape:\n"
        f"- Start with a heading exactly like: ### [{division_acronym}] {division}\n"
        "- Then follow the selected answer-mode prompt exactly.\n\n"
        f"{_mode_reduce_prompt(answer_mode, answer_mode_flags)}\n\n"
        f"Question:\n{question}\n\n"
        f"Division: {division}\n\n"
        f"Figure Handle registry status:\n{annotation_context}\n\n"
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
        f"{FIGURE_HANDLE_RULES}\n\n"
        f"{_mode_synthesis_prompt(answer_mode, answer_mode_flags)}\n\n"
        f"Question:\n{question}\n\n"
        f"Figure Handle registry status:\n{annotation_context}\n\n"
        f"Division answers:\n{division_context}"
    )
