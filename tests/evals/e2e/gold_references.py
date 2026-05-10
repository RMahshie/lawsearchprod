"""Gold standard references for e2e eval judging.

Each entry maps a question ID (from questions.py) to a GoldReference
containing the facts the answer must include, errors it must avoid,
and the expected classify/route outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GoldReference:
    required_facts: list[str] = field(default_factory=list)
    prohibited_errors: list[str] = field(default_factory=list)
    expected_answer_mode: str = ""
    expected_divisions: list[str] = field(default_factory=list)
    notes: str = ""


GOLD_REFERENCES: dict[str, GoldReference] = {
    # ------------------------------------------------------------------
    # direct_account_amount
    # ------------------------------------------------------------------

    "direct_1": GoldReference(
        required_facts=[
            "FDA Salaries and Expenses is appropriated $6,957,972,000",
            "Major uses include Human Foods Program, CDER, CBER, CVM, CDRH, NCTR, Center for Tobacco Products, rent/related activities, and other central FDA offices/services",
            "User fees are credited to the account, including prescription drug, medical device, human generic drug, biosimilar, animal drug, generic new animal drug, and tobacco product user fees",
        ],
        prohibited_errors=[
            "Should not list center-by-center dollar amounts unless the user asked for a breakdown",
            "Should not list individual user-fee dollar amounts unless the user asked for a user-fee breakdown",
            "Should not add user fees on top of the $6,957,972,000 account amount",
            "Should not include unrelated nearby provisions",
            "Should not use internal pipeline language like extracted facts, retrieved facts, mapped facts, or source chunks",
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="Compact account amount/use question. Do not turn this into reconciliation mode.",
    ),

    "direct_2": GoldReference(
        required_facts=[
            "Food Safety and Inspection Service is appropriated $1,215,200,000",
            "The funding carries out services authorized by the Federal Meat Inspection Act, Poultry Products Inspection Act, and Egg Products Inspection Act",
            "$1,000,000 may be credited to the account from laboratory accreditation fees",
            "Major activities include inspection and enforcement for meat, poultry, and egg products",
            "Major activities include humane methods of slaughter inspections and enforcement",
        ],
        prohibited_errors=[
            "Should not treat the $10,000 representation allowance cap as a separate major appropriation",
            "Should not add the $1,000,000 laboratory accreditation fees as a separate appropriation without saying they may be credited to the account",
            "Should not route outside Agriculture",
            "Should not turn the answer into a detailed reconciliation ledger",
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="Amount + activities. The $10,000 is a cap; the $1,000,000 is credited fee authority.",
    ),

    "direct_3": GoldReference(
        required_facts=[
            "NASA Science is appropriated $7,250,000,000",
            "The funding is for necessary expenses in the conduct and support of science research and development activities",
            "The funding remains available until September 30, 2027",
        ],
        prohibited_errors=[
            "Should not include unrelated NASA accounts such as Aeronautics, Exploration, Space Operations, SSMS, Construction, or OIG",
            "Should not compute a NASA-wide total",
            "Should not confuse NASA Science with another NASA account",
            "Should not route outside Commerce, Justice, Science",
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES",
        ],
        notes="One named NASA account only.",
    ),

    "direct_4": GoldReference(
        required_facts=[
            "EPA Environmental Programs and Management is appropriated $3,114,671,000",
            "The funding remains available until September 30, 2027",
            "The account supports necessary expenses for personnel, travel, passenger motor vehicles, aircraft, reprints, library memberships, and administrative costs",
            "The account supports administrative costs of the brownfields program and implementation of a coal combustion residual permit program",
            "Major set-asides include Energy Star, grants/projects/implementation/training, and Environmental Protection: National Priorities",
            "Major set-asides include Geographic Programs $690,202,000",
        ],
        prohibited_errors=[
            "Should not imply the full $3,114,671,000 is brownfields cleanup funding",
            "Should not add set-asides on top of the parent account total",
            "Should not over-focus on the $40,000 official reception cap",
            "Should not route outside Interior/Environment",
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
        ],
        notes="Direct account amount, with compact support-purpose summary.",
    ),

    "direct_5": GoldReference(
        required_facts=[
            "VA Medical Services amount directly paired with the care scope is $59,858,000,000",
            "The amount is for FY2026 plus reimbursements",
            "Covered services include priority medical treatment and basic medical benefits for veterans in priority groups 1 through 6",
            "Covered services include prescription drugs, prosthetics, women veterans care, suicide prevention, caregiver support, PTSD services, rural health care, homelessness programs, telehealth, opioid prevention and treatment, and intimate partner violence assistance",
        ],
        prohibited_errors=[
            "Should not merge multiple VA Medical Services figures without explaining the ambiguity",
            "Should not use internal language like extracted facts in the final answer",
            "Should not confuse VA Medical Services with Medical Community Care or other VA medical accounts",
            "Should not route outside Military Construction, Veterans Affairs",
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES",
        ],
        notes="Gold should allow a careful uncertainty phrase, but not internal pipeline wording.",
    ),

    # ------------------------------------------------------------------
    # broad_topic_total
    # ------------------------------------------------------------------

    "broad_1": GoldReference(
        required_facts=[
            "No single clean FY2026 total is available because the funding mixes appropriated grant/subsidy amounts, loan subsidy cost, direct loan authority, guaranteed loan authority, and authorization changes",
            "USDA Rural Utilities Service Rural Water and Waste Disposal Program Account is a core controlling account",
            "USDA RUS includes $445,864,564 for the cost of direct loans, loan guarantees, and grants",
            "USDA RUS includes $1,015,000,000 in direct loan authority and $50,000,000 in guaranteed loan authority",
            "USDA rural water and waste technical assistance grants include $35,000,000",
            "EPA State and Tribal Assistance Grants include Clean Water SRF capitalization grants of $1,638,861,000",
            "EPA State and Tribal Assistance Grants include Drinking Water SRF capitalization grants of $1,126,101,000",
            "EPA includes $35,000,000 for U.S.-Mexico border water and wastewater facilities",
            "EPA includes $39,000,000 for Alaska rural and Alaska Native Village drinking water and wastewater infrastructure needs",
            "EPA WIFIA includes $64,634,000 for the cost of direct loans and guaranteed loans",
            "EWD includes a Northwestern New Mexico Rural Water Projects Act authorization increase from $870,000,000 to $1,815,000,000, but it is not a clean FY2026 appropriation",
        ],
        prohibited_errors=[
            "Should not present one clean additive total",
            "Should not add USDA loan authority to USDA subsidy/grant budget authority",
            "Should not add STAG total to SRF sub-buckets or project-specific suballocations",
            "Should not treat WIFIA loan subsidy cost and WIFIA principal cap as additive",
            "Should not omit EPA/Interior for rural water or wastewater infrastructure",
            "Should not treat an authorization increase as directly available FY2026 appropriations",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
            "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES",
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
        ],
        notes="Key cross-division broad-topic benchmark. Reward grouped funding lanes and financial-type labels.",
    ),

    "broad_2": GoldReference(
        required_facts=[
            "THUD provides separate FY2026 funding streams for rental assistance and homelessness services",
            "Tenant-based rental assistance is appropriated $34,438,557,000",
            "Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025",
            "Tenant-based rental assistance includes $4,000,000,000 available October 1, 2026",
            "Tenant-based rental assistance includes $34,957,000,000 for renewals of expiring Section 8 tenant-based annual contributions contracts",
            "Project-based rental assistance is provided $18,143,000,000",
            "Homeless Assistance Grants receive $4,417,000,000",
            "Homeless Assistance Grants include $290,000,000 for Emergency Solutions Grants",
            "Homeless Assistance Grants include $4,010,000,000 for Continuum of Care and rural housing stability assistance",
            "Homeless Assistance Grants include $10,000,000 for national homeless data analysis",
            "Homelessness services include $107,000,000 for youth homelessness demonstration projects",
            "Youth homelessness system improvement grants may receive up to $25,000,000",
            "Supportive housing for persons with disabilities includes $287,000,000 for Section 811 project rental assistance and associated supportive services",
            "Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding",
        ],
        prohibited_errors=[
            "Should not present a single clean city housing total",
            "Should not add renewal amounts, advance appropriations, and parent amounts without explaining timing and hierarchy",
            "Should not add the $25,000,000 youth homelessness improvement amount on top of the $107,000,000 parent amount",
            "Should not omit homelessness services when the question asks affordable housing, rental assistance, or homelessness services",
            "Should not omit the main Homeless Assistance Grants parent account when answering homelessness services",
            "Should not route outside THUD unless there is clearly responsive evidence elsewhere",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES",
        ],
        notes="The answer should be organized by HUD program/funding lane, not as one additive total.",
    ),

    "broad_3": GoldReference(
        required_facts=[
            "Airport infrastructure funding is available through airport grants in THUD",
            "Airport and Airway Trust Fund grants-in-aid for airport planning and development are $4,000,000,000",
            "The $4,000,000,000 supports grants-in-aid for airport planning and development, runway incursion prevention devices and systems, and related airport safety activities",
            "Additional Grants-In-Aid for Airports amount is $577,356,000",
            "$542,356,000 is for Community Project Funding or Congressionally Directed Spending for airport projects",
            "Up to $35,000,000 is for discretionary grants to airports for eligible projects",
            "$542,356,000 and $35,000,000 are suballocations within the $577,356,000 airport-grants heading",
        ],
        prohibited_errors=[
            "Should not add $542,356,000 and $35,000,000 on top of the $577,356,000 parent amount",
            "Should not claim a clean total unless it clearly explains the relationship between the $4,000,000,000 and $577,356,000 buckets",
            "Should not omit runway improvements or terminal upgrades",
            "Should not route outside THUD",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES",
        ],
        notes="A clean sum of the two top-level airport buckets may be acceptable only if the answer clearly does not double-count suballocations. Runway improvements and terminal upgrades are responsive examples when source-backed by project-table evidence.",
    ),

    "broad_4": GoldReference(
        required_facts=[
            "Local law enforcement, community violence prevention, and police hiring funding is primarily in OJP and COPS",
            "OJP is $2,400,000,000",
            "OJP includes $964,000,000 for the Edward Byrne Memorial JAG program",
            "COPS programs total $800,000,000",
            "COPS includes $253,093,613 for hiring and rehiring additional career law enforcement officers",
            "COPS includes $84,000,000 for police-community relations",
            "COPS includes $50,000,000 for community violence intervention and prevention",
            "COPS includes $18,000,000 for community policing development",
            "COPS includes $15,000,000 for de-escalation training",
            "COPS includes $32,000,000 for Tribal law enforcement hiring and activities",
            "Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program",
        ],
        prohibited_errors=[
            "Should not present one clean additive total of all listed figures",
            "Should not add nested COPS program amounts on top of the $800,000,000 COPS total",
            "Should not add Byrne JAG on top of OJP as if it were separate from OJP",
            "Should not omit either OJP/Byrne JAG or COPS hiring/community violence funding",
            "Should not route outside CJS",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES",
        ],
        notes="Must preserve parent-child relationships for OJP/JAG and COPS subprograms.",
    ),

    "broad_5": GoldReference(
        required_facts=[
            "No clean division-wide total is supported because amounts mix separate accounts, grants, and broader management funding",
            "Hazardous Substance Superfund is $282,749,000 for necessary expenses to carry out CERCLA, including cleanup activities",
            "CERCLA section 104(k) brownfields grants are $98,000,000",
            "CERCLA section 128 grants are $46,250,000",
            "Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000",
            "Environmental Programs and Management is $3,114,671,000 and includes administrative costs of the brownfields program, but it is broader than cleanup funding",
            "Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities",
            "EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided",
        ],
        prohibited_errors=[
            "Should not present one clean additive brownfields/Superfund/remediation total",
            "Should not imply the full Environmental Programs and Management account is cleanup funding",
            "Should not treat fee authority with no stated dollar amount as a quantified funding line",
            "Should not omit Hazardous Substance Superfund or brownfields grants",
            "Should not route outside Interior/Environment",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
        ],
        notes="Good answer separates direct cleanup/remediation accounts from broader EPM support.",
    ),

    # ------------------------------------------------------------------
    # funding_mechanism_no_amount
    # ------------------------------------------------------------------

    "mechanism_1": GoldReference(
        required_facts=[
            "DHS funding is handled through continuing appropriations rather than a full-year DHS appropriation",
            "The continuing resolution uses a rate-for-operations framework tied to prior-year appropriations",
            "The continuing appropriations authority is extended through February 13, 2026",
            "No consolidated full-year DHS dollar amount is provided in the FY2026 laws",
        ],
        prohibited_errors=[
            "Should not hallucinate a full-year DHS amount",
            "Should not add DHS component extensions into a DHS total",
            "Should not classify this as a normal broad funding total",
            "Should not route outside Continuing Appropriations, Extenders, Homeland Security, and Other Matters",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Override current classifier if it says broad_topic_total. This is a no-explicit-amount CR mechanism question.",
    ),

    "mechanism_2": GoldReference(
        required_facts=[
            "The Further Continuing Appropriations Act, 2026 extends continuing appropriations for FY2026",
            "It changes or extends the operative expiration date in the continuing appropriations framework",
            "It is a continuing resolution measure, not a full-year appropriations bill",
            "The core continuing appropriations mechanism is rate for operations under FY2025 appropriations acts and conditions",
        ],
        prohibited_errors=[
            "Should not invent a total dollar amount for the Further Continuing Appropriations Act",
            "Should not treat the CR as a normal full-year appropriations division",
            "Should not omit rate-for-operations language",
            "Should not route outside Continuing Appropriations, Extenders, Homeland Security, and Other Matters",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Even though the question is explanatory, the important behavior is mechanism-with-no-new-total.",
    ),

    "mechanism_3": GoldReference(
        required_facts=[
            "No explicit FEMA Disaster Relief Fund dollar total was found in the FY2026 continuing appropriations text",
            "FEMA Disaster Relief Fund is handled through continuing appropriations rather than a new explicit DRF dollar figure",
            "The continuing appropriations period is extended to February 13, 2026",
            "DRF amounts may be apportioned up to the rate for operations necessary for Stafford Act response and recovery activities",
            "The mechanism uses FY2025 appropriations acts as the reference for the rate-for-operations framework",
            "Prior disaster-relief designations are preserved for amounts incorporated by reference",
        ],
        prohibited_errors=[
            "Should not invent a new FY2026 DRF dollar amount",
            "Should not substitute unrelated FEMA amounts from elsewhere",
            "Should not present a FEMA total without a source-backed current-year amount",
            "Should not route outside Continuing Appropriations, Extenders, Homeland Security, and Other Matters",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Classic mechanism/no-explicit-dollar test.",
    ),

    "mechanism_4": GoldReference(
        required_facts=[
            "The FY2026 text does not provide a specific CISA dollar amount in the identified provisions",
            "CISA is described through a continuing-appropriations mechanism",
            "The continuing resolution date is extended to February 13, 2026",
            "Funding uses FY2025 rate-for-operations language",
            "A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions",
        ],
        prohibited_errors=[
            "Should not hallucinate a CISA dollar amount",
            "Should not substitute a broader DHS amount for CISA",
            "Should not treat CR extension language as a dollar amount",
            "Should not route outside Continuing Appropriations, Extenders, Homeland Security, and Other Matters",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Should answer the either/or directly: only mechanism, no specific CISA amount.",
    ),

    "mechanism_5": GoldReference(
        required_facts=[
            "Agencies or accounts without full-year appropriations continue operating under the continuing resolution",
            "They continue at the FY2025 rate and under the authority and conditions of applicable FY2025 appropriations Acts",
            "The continuation applies to continuing projects and activities through the date specified in section 106(3)",
            "They may continue only at the most limited funding action permitted",
            "The Act allows certain payments and obligations to continue, including personnel pay and benefits, mandatory payments, essential activities to protect life and property, and orderly termination of government functions",
            "Payments and reimbursements are made only to the extent and in the amounts provided in advance in appropriations Acts",
        ],
        prohibited_errors=[
            "Should not provide a new dollar amount",
            "Should not imply agencies receive a full-year appropriation",
            "Should not omit the FY2025 rate/authority/conditions concept",
            "Should not route outside Continuing Appropriations, Extenders, Homeland Security, and Other Matters",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="This is explanatory, but for eval purposes it should test CR mechanism behavior.",
    ),

    # ------------------------------------------------------------------
    # reconciliation_breakdown
    # ------------------------------------------------------------------

    "recon_1": GoldReference(
        required_facts=[
            "FDA Salaries and Expenses total appropriation is $6,957,972,000",
            "Programmatic breakdown includes Human Foods Program $1,171,319,000",
            "Programmatic breakdown includes CDER $2,496,766,000",
            "Programmatic breakdown includes CBER $601,291,000",
            "Programmatic breakdown includes CVM $278,185,000",
            "Programmatic breakdown includes CDRH $894,063,000",
            "Programmatic breakdown includes NCTR $71,758,000",
            "Programmatic breakdown includes Center for Tobacco Products $688,038,000",
            "Programmatic breakdown includes Rent and Related $205,180,000",
            "Programmatic breakdown includes GSA rent payments $208,018,000",
            "Programmatic breakdown includes Other activities $343,354,000",
            "Programmatic allocations reconcile to $6,957,972,000",
            "Financing-source breakdown includes prescription drug user fees $1,556,039,000",
            "Financing-source breakdown includes medical device user fees $478,166,000",
            "Financing-source breakdown includes human generic drug user fees $670,900,000",
            "Financing-source breakdown includes biosimilar biological product user fees $55,841,000",
            "Financing-source breakdown includes animal drug user fees $36,152,000",
            "Financing-source breakdown includes generic new animal drug user fees $26,724,000",
            "Financing-source breakdown includes tobacco product user fees $712,000,000",
            "User-fee amounts are credited to the same account and should not be added on top of the account total",
            "$15,000,000 foreign seafood inspections is within Human Foods",
            "$10,000,000 foreign inspection pilots is within CDER",
            "$44,400,000 White Oak Consolidation is within Rent and Related",
            "$25,000 is a ceiling on official reception and representation expenses",
            "$2,000,000 is a transfer cap, not new budget authority",
            "$1,500,000 transfer to HHS OIG is not a separate addition to FDA Salaries and Expenses",
            "FY2027 user fees accepted in FY2026 are excluded from FY2026 amounts under this heading",
        ],
        prohibited_errors=[
            "Should not add user-fee source amounts on top of the $6,957,972,000 account total",
            "Should not classify the $25,000 reception ceiling as a suballocation instead of a cap/limitation",
            "Should not add $44,400,000 White Oak on top of the Rent and Related line",
            "Should not add $15,000,000 or $10,000,000 set-asides on top of their parent lines",
            "Should not surface malformed extraction labels like source cut off or additional user fee source cut off",
            "Should not invent one-to-one mappings between user-fee sources and FDA centers",
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="Core reconciliation benchmark. Must separate programmatic allocations from financing-source/user-fee amounts.",
    ),

    "recon_2": GoldReference(
        required_facts=[
            "NASA major accounts include Science $7,250,000,000",
            "NASA major accounts include Aeronautics $935,000,000",
            "NASA major accounts include Space Technology $920,500,000",
            "NASA major accounts include Exploration $7,783,000,000",
            "NASA major accounts include Space Operations $4,175,000,000",
            "NASA major accounts include STEM Engagement $143,000,000",
            "NASA major accounts include Safety, Security and Mission Services $3,000,000,000",
            "NASA major accounts include Construction and Environmental Compliance and Restoration $185,336,000",
            "NASA major accounts include Office of Inspector General $46,500,000",
            "$58,417,135 is Community Project Funding/Congressionally Directed Spending within SSMS, not added separately",
            "$2,500,000 is a set-aside within the $46,500,000 OIG total",
            "$33,000,000 lease-proceeds availability cap is inside CECR and is not standalone budget authority",
            "Up to $38,500,000 may be transferred from SSMS to NASA's Working Capital Fund, but that is transfer authority, not new funding",
            "CECR prior-year project use is limited to not more than 20 percent or $50,000,000, whichever is less",
            "Use the statutory NASA Science account amount unless the answer explicitly explains and cites any conflicting explanatory-statement figure",
        ],
        prohibited_errors=[
            "Should not add suballocations such as $58,417,135 or $2,500,000 on top of parent NASA account totals",
            "Should not treat lease proceeds or transfer authority as new appropriations",
            "Should not merge conflicting Science figures without acknowledging the conflict",
            "Should not route outside Commerce, Justice, Science",
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES",
        ],
        notes="NASA reconciliation should focus on account totals and non-additive suballocations/transfers, not force a clean NASA grand total if evidence is conflicted.",
    ),

    "recon_3": GoldReference(
        required_facts=[
            "USDA Rural Water and Waste Disposal Program Account states $1,015,000,000 in direct-loan authority",
            "USDA Rural Water and Waste Disposal Program Account states $50,000,000 in guaranteed-loan authority",
            "USDA Rural Water and Waste Disposal Program Account states $445,864,564 in subsidy/grant budget authority",
            "Direct and guaranteed loan authority total $1,065,000,000",
            "The two explicitly listed TA/circuit-rider lines total $58,900,000: $35,000,000 rural water and waste technical assistance grants plus $23,900,000 circuit rider",
            "$51,476,000 is for direct loans",
            "$3,876,000 is a floor within the $51,476,000 direct-loan set-aside",
            "$1,000,000 is for rural utilities program under section 306(a)(2)(B)",
            "$5,000,000 is for section 306E rural utilities activity",
            "$1,000,000 within section 306E is for subgrants for household decentralized wastewater systems",
            "$7,000,000 is for section 306A(i)(2) grants",
            "$60,000,000 is for loans and grants including water and waste disposal systems grants and Native/tribal/Hawaiian Home Lands purposes",
            "$35,000,000 is for rural water and waste technical assistance grants",
            "$10,000,000 is within the $35,000,000 technical-assistance line",
            "$800,000 is within the $35,000,000 technical-assistance line",
            "$23,900,000 is for the circuit rider program",
            "$4,000,000 is for solid waste management grants",
            "$250,488,564 is a grant line",
            "$110,488,564 is Community Project Funding/Congressionally Directed Spending within the $250,488,564 grant line",
            "$8,000,000 is a transfer to the Rural Utilities Service High Energy Cost Grants Account",
            "0.25 percent management/oversight retention is a cap or limitation",
        ],
        prohibited_errors=[
            "Should not add $1,015,000,000 direct loans, $50,000,000 guaranteed loans, and $445,864,564 subsidy/grant budget authority into one clean pool",
            "Should not add $3,876,000 on top of the $51,476,000 parent line",
            "Should not add $10,000,000 or $800,000 on top of the $35,000,000 technical-assistance parent line",
            "Should not add $110,488,564 on top of the $250,488,564 grant line",
            "Should not treat the $8,000,000 transfer as new funding",
            "Should not treat the 0.25 percent oversight retention as a funding line",
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="This is the best test for financial-type labeling: loan authority vs subsidy/grant budget authority vs transfer/cap.",
    ),

    "recon_4": GoldReference(
        required_facts=[
            "EPA State and Tribal Assistance Grants account totals $4,409,609,000",
            "The answer should not provide a derived water-infrastructure subtotal unless it lists the exact source-backed components included in that subtotal",
            "Clean Water SRF capitalization grants are $1,638,861,000",
            "Drinking Water SRF capitalization grants are $1,126,101,000",
            "Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000",
            "Safe Drinking Water Act section 1464(d) grants are $28,000,000",
            "STAG includes section 1459B grants of $22,000,000",
            "STAG includes section 1459A(l) grants of $6,500,000",
            "STAG includes FWPCA section 104(b)(8) grants of $25,500,000",
            "STAG includes FWPCA section 221 grants of $41,000,000",
            "STAG includes America's Water Infrastructure Act section 4304(b) grants of $5,400,000",
            "STAG includes Save Our Seas section 302(a) grants of $3,500,000",
            "STAG includes CPF/CDS remediation, construction, and environmental management projects of $20,364,000",
            "U.S.-Mexico Border high-priority water and wastewater facilities are $35,000,000",
            "Alaska rural and Alaska Native Village drinking water and wastewater infrastructure needs are $39,000,000",
            "SRF and project-specific amounts sit within the broader STAG account structure",
            "The STAG account includes non-water items outside this breakdown",
        ],
        prohibited_errors=[
            "Should not add the $4,409,609,000 STAG total to SRF and project-specific amounts",
            "Should not double-count project-specific amounts that are within the same broader STAG structure",
            "Should not present STAG's full $4,409,609,000 as entirely water infrastructure",
            "Should not assert a derived STAG water subtotal unless the listed components reconcile to it",
            "Should not omit either Clean Water SRF or Drinking Water SRF",
            "Should not route outside Interior/Environment",
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
        ],
        notes="Do not force a derived water-infrastructure subtotal unless the answer explicitly lists and reconciles the included components.",
    ),

    "recon_5": GoldReference(
        required_facts=[
            "IRS breakdown belongs in Financial Services and General Government",
            "IRS Taxpayer Services receives $3,036,606,000",
            "IRS Enforcement receives $4,999,000,000",
            "IRS Technology and Operations Support receives $3,159,759,000",
            "No separate FY2026 dollar amount for Business Systems Modernization appears in the available text",
            "$7,000,000 is within the Taxpayer Advocate Service amount for identity theft and refund fraud casework",
            "$250,000,000 remains available within Enforcement and is not added on top",
            "$60,257,000 is within Enforcement for the Interagency Crime and Drug Enforcement program",
            "Enforcement includes not more than $35,000,000 for Criminal Investigation investigative technology",
            "$275,000,000 remains available within Technology and Operations Support and is not added on top",
            "$10,000,000 is within Technology and Operations Support for equipment and facilities acquisition",
            "$1,000,000 is within Technology and Operations Support for research",
            "$20,000 is within Technology and Operations Support for official reception and representation expenses",
            "Transfer authority of up to 5 percent of IRS funds is a limitation on use, not a separate FY2026 funding amount",
        ],
        prohibited_errors=[
            "Should not invent a Business Systems Modernization dollar amount if none appears",
            "Should not add within-account set-asides on top of their parent IRS account amounts",
            "Should not treat the 5 percent transfer authority as new funding",
            "Should not classify official reception and representation as a separate funding line",
            "Should not route outside Financial Services and General Government",
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "FINANCIAL SERVICES AND GENERAL GOVERNMENT",
        ],
        notes="Use this to catch hallucinated BSM amounts and parent/child double counting in IRS.",
    ),

    # ------------------------------------------------------------------
    # general_summary
    # ------------------------------------------------------------------

    "summary_1": GoldReference(
        required_facts=[
            "The FY2026 Agriculture division funds FDA salaries and expenses",
            "FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products",
            "The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment",
            "The division bars use of funds to implement electronic distribution of prescribing information for certain drugs unless federal law authorizes it",
        ],
        prohibited_errors=[
            "Should not turn the answer into a reconciliation ledger",
            "Should not list every FDA center/activity dollar amount",
            "Should not list every user-fee dollar amount",
            "Should not omit the electronic prescribing-information restriction",
            "Should not route outside Agriculture",
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="Plain-English summary. Numbers are optional unless directly helpful.",
    ),

    "summary_2": GoldReference(
        required_facts=[
            "Energy and Water Development supports Department of Energy programs and water-related programs",
            "Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities",
            "Supported water and civil works activities include hydroelectric facility operations and upgrades",
            "Supported water activities include Bureau of Reclamation and water storage or restoration projects",
            "Supported water activities include regulatory program activities for navigable waters and wetlands",
            "Supported cleanup/emergency activities include formerly utilized sites cleanup and flood control or coastal emergencies",
            "The division also funds administration and oversight, including Departmental Administration and the Office of Inspector General",
        ],
        prohibited_errors=[
            "Should not turn the summary into a dollar-by-dollar account ledger",
            "Should not focus only on DOE and omit water/civil works",
            "Should not focus only on water and omit DOE energy programs",
            "Should not route outside Energy and Water Development",
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES",
        ],
        notes="General project/activity summary. No need for numeric totals.",
    ),

    "summary_3": GoldReference(
        required_facts=[
            "Water infrastructure appears across USDA, EPA, and Energy-Water",
            "USDA supports rural water and waste disposal through Rural Utilities Service loans, guarantees, grants, and technical assistance",
            "EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA",
            "Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material",
            "The answer should explain that these are different funding mechanisms and should not be collapsed into a single clean total",
        ],
        prohibited_errors=[
            "Should not provide a detailed dollar-by-dollar breakdown",
            "Should not present one clean total across USDA, EPA, and Energy-Water",
            "Should not omit one of USDA, EPA, or Energy-Water",
            "Should not confuse loan authority, grant funding, loan subsidy cost, and authorization changes",
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
            "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES",
        ],
        notes="Summary version of broad_1. Should explain landscape without full ledger.",
    ),

    "summary_4": GoldReference(
        required_facts=[
            "Regular appropriations provide full-year funding for specified accounts and programs",
            "Continuing appropriations temporarily extend funding for agencies or accounts without full-year appropriations",
            "Continuing appropriations generally operate at a prior-year rate for operations",
            "Continuing appropriations preserve prior-law authority and conditions for continuing projects and activities",
            "A continuing resolution is not the same as a new full-year line-item appropriation",
        ],
        prohibited_errors=[
            "Should not invent a dollar amount for continuing appropriations",
            "Should not imply continuing appropriations are full-year regular appropriations",
            "Should not omit rate-for-operations concept",
            "Should not route outside Continuing Appropriations when explaining CR mechanics",
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Conceptual explanation. It can mention regular divisions generally, but CRX is the controlling source for continuing appropriations mechanics.",
    ),

    "summary_5": GoldReference(
        required_facts=[
            "Transportation-HUD covers transportation and housing/urban development programs relevant to local governments",
            "Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs",
            "HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs",
            "The division contains distinct accounts and programs rather than one single local-government funding pool",
            "The answer should be concise and explanatory rather than a detailed funding ledger",
        ],
        prohibited_errors=[
            "Should not compute a THUD-wide total",
            "Should not list every THUD account amount",
            "Should not omit either transportation or housing/HUD coverage",
            "Should not route outside THUD",
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES",
        ],
        notes="Plain-English local-government summary of THUD scope.",
    ),
}
