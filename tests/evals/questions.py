"""Test questions for embedding model evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field


AG = "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES"
CJS = "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES"
INT = "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES"
EWD = "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES"
MCVA = "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES"
THUD = "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES"
CRX = "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"
FSGG = "FINANCIAL SERVICES AND GENERAL GOVERNMENT"


@dataclass(frozen=True)
class EvalQuestion:
    id: str
    question: str
    answer_mode: str
    divisions: list[str] = field(default_factory=list)
    expected_behavior: str = ""


EVAL_QUESTIONS: list[EvalQuestion] = [
    # ── direct_account_amount ──
    EvalQuestion(
        id="direct_1",
        question="What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?",
        answer_mode="direct_account_amount",
        divisions=[AG],
        expected_behavior="Main amount + compact use summary; no ledger unless asked.",
    ),
    EvalQuestion(
        id="direct_2",
        question="What amount is provided for the USDA Food Safety and Inspection Service in FY2026, and what activities does it fund?",
        answer_mode="direct_account_amount",
        divisions=[AG],
        expected_behavior="Main amount + compact use summary; no ledger unless asked.",
    ),
    EvalQuestion(
        id="direct_3",
        question="What amount is appropriated for NASA Science in FY2026, and what is the funding available for?",
        answer_mode="direct_account_amount",
        divisions=[CJS],
        expected_behavior="Main amount + compact use summary; no ledger unless asked.",
    ),
    EvalQuestion(
        id="direct_4",
        question="What amount is appropriated for the EPA Environmental Programs and Management account in FY2026, and what does that account support?",
        answer_mode="direct_account_amount",
        divisions=[INT],
        expected_behavior="Main amount + compact use summary; no ledger unless asked.",
    ),
    EvalQuestion(
        id="direct_5",
        question="What VA Medical Services amounts are identified for FY2026, how are their availability dates described, and what kinds of care or services do the provisions cover?",
        answer_mode="direct_account_amount",
        divisions=[MCVA],
        expected_behavior="Report the dated Medical Services tranches and pooled-care scope without collapsing separate VA accounts; no ledger unless asked.",
    ),

    # ── broad_topic_total ──
    EvalQuestion(
        id="broad_1",
        question="What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it?",
        answer_mode="broad_topic_total",
        divisions=[AG, INT, EWD],
        expected_behavior="Grouped funding lanes by agency/account; label financial types; no fake total when mixed types.",
    ),
    EvalQuestion(
        id="broad_2",
        question="What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?",
        answer_mode="broad_topic_total",
        divisions=[THUD],
        expected_behavior="Grouped funding lanes by agency/account; label financial types; no fake total when mixed types.",
    ),
    EvalQuestion(
        id="broad_3",
        question="What FY2026 funding is available for airport infrastructure, runway or airport-safety improvements, and airport project grants?",
        answer_mode="broad_topic_total",
        divisions=[THUD],
        expected_behavior="Grouped airport funding lanes by heading; distinguish project grants from administrative support; do not infer terminal construction without source support.",
    ),
    EvalQuestion(
        id="broad_4",
        question="What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?",
        answer_mode="broad_topic_total",
        divisions=[CJS],
        expected_behavior="Grouped funding lanes by agency/account; label financial types; no fake total when mixed types.",
    ),
    EvalQuestion(
        id="broad_5",
        question="What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?",
        answer_mode="broad_topic_total",
        divisions=[INT],
        expected_behavior="Grouped funding lanes by agency/account; label financial types; no fake total when mixed types.",
    ),

    # ── funding_mechanism_no_amount ──
    EvalQuestion(
        id="mechanism_1",
        question="How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?",
        answer_mode="funding_mechanism_no_amount",
        divisions=[CRX],
        expected_behavior="Explain CR/rate-for-operations/apportionment/extension; say when no explicit amount found.",
    ),
    EvalQuestion(
        id="mechanism_2",
        question="What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?",
        answer_mode="funding_mechanism_no_amount",
        divisions=[CRX],
        expected_behavior="Explain CR/rate-for-operations/apportionment/extension; say when no explicit amount found.",
    ),
    EvalQuestion(
        id="mechanism_3",
        question="How does FY2026 handle FEMA Disaster Relief Fund funding under continuing appropriations?",
        answer_mode="funding_mechanism_no_amount",
        divisions=[CRX],
        expected_behavior="Explain CR/rate-for-operations/apportionment/extension; say when no explicit amount found.",
    ),
    EvalQuestion(
        id="mechanism_4",
        question="Within the identified FY2026 continuing-appropriations provisions, is a specific CISA dollar amount stated, or is only a continuing-appropriations mechanism supported?",
        answer_mode="funding_mechanism_no_amount",
        divisions=[CRX],
        expected_behavior="Explain CR/rate-for-operations/apportionment/extension; say when no explicit amount found.",
    ),
    EvalQuestion(
        id="mechanism_5",
        question="What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?",
        answer_mode="funding_mechanism_no_amount",
        divisions=[CRX],
        expected_behavior="Explain CR/rate-for-operations/apportionment/extension; say when no explicit amount found.",
    ),

    # ── reconciliation_breakdown ──
    EvalQuestion(
        id="recon_1",
        question="Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what should not be added separately.",
        answer_mode="reconciliation_breakdown",
        divisions=[AG],
        expected_behavior="Included / Not Added Separately / Caveats; preserve parent-child math.",
    ),
    EvalQuestion(
        id="recon_2",
        question="Break down NASA FY2026 funding by major account, and explain which amounts can be summed versus which are suballocations or transfers.",
        answer_mode="reconciliation_breakdown",
        divisions=[CJS],
        expected_behavior="Included / Not Added Separately / Caveats; preserve parent-child math.",
    ),
    EvalQuestion(
        id="recon_3",
        question="Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical assistance, and set-asides. What should not be added together?",
        answer_mode="reconciliation_breakdown",
        divisions=[AG],
        expected_behavior="Included / Not Added Separately / Caveats; preserve parent-child math.",
    ),
    EvalQuestion(
        id="recon_4",
        question="Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and project-specific amounts. What should not be double-counted?",
        answer_mode="reconciliation_breakdown",
        divisions=[INT],
        expected_behavior="Included / Not Added Separately / Caveats; preserve parent-child math.",
    ),
    EvalQuestion(
        id="recon_5",
        question="Break down IRS FY2026 funding by taxpayer services, enforcement, operations support, and business systems modernization, and explain whether those amounts reconcile to a parent total.",
        answer_mode="reconciliation_breakdown",
        divisions=[FSGG],
        expected_behavior="Included / Not Added Separately / Caveats; preserve parent-child math.",
    ),

    # ── general_summary ──
    EvalQuestion(
        id="summary_1",
        question="In plain English, what does the FY2026 Agriculture division do for the FDA?",
        answer_mode="general_summary",
        divisions=[AG],
        expected_behavior="Concise prose or short bullets; no forced ledger; numbers only if directly relevant.",
    ),
    EvalQuestion(
        id="summary_2",
        question="What kinds of projects or activities does the Energy and Water Development division generally support?",
        answer_mode="general_summary",
        divisions=[EWD],
        expected_behavior="Concise prose or short bullets; no forced ledger; numbers only if directly relevant.",
    ),
    EvalQuestion(
        id="summary_3",
        question="Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detailed dollar breakdown.",
        answer_mode="general_summary",
        divisions=[AG, INT, EWD],
        expected_behavior="Concise prose or short bullets; no forced ledger; numbers only if directly relevant.",
    ),
    EvalQuestion(
        id="summary_4",
        question="What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?",
        answer_mode="general_summary",
        divisions=[CRX],
        expected_behavior="Concise prose or short bullets; no forced ledger; numbers only if directly relevant.",
    ),
    EvalQuestion(
        id="summary_5",
        question="Summarize what the FY2026 Transportation-HUD division covers for local governments.",
        answer_mode="general_summary",
        divisions=[THUD],
        expected_behavior="Concise prose or short bullets; no forced ledger; numbers only if directly relevant.",
    ),
]
