# E2E Eval Report

## Overall Summary

- **Questions**: 25 (25 scored)
- **Avg Score**: 7.5 / 10
- **Fact Recall**: 81.5%
- **Error Rate**: 3.5%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 5 | 5.6 | 76.5% | 3.8% | 100.0% | 100.0% |
| direct_account_amount | 5 | 7.4 | 66.7% | 0.0% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 5 | 9.0 | 84.0% | 0.0% | 100.0% | 100.0% |
| general_summary | 5 | 8.2 | 76.9% | 0.0% | 100.0% | 100.0% |
| reconciliation_breakdown | 5 | 7.4 | 88.2% | 11.1% | 100.0% | 100.0% |

## Per-Question Detail

### direct_1 (score: 8)

**Question**: What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- User fees are credited to the account, including prescription drug, medical device, human generic drug, biosimilar, animal drug, generic new animal drug, and tobacco product user fees

**Judge Reasoning**: The answer correctly provides the appropriation amount and lists the major allowed uses, and follows mode-specific structural rules. However, it omits 'animal drug' and 'generic new animal drug' user fees from the user-fee list, a required fact. No prohibited errors were triggered.

### direct_2 (score: 7)

**Question**: What amount is provided for the USDA Food Safety and Inspection Service in FY2026, and what activities does it fund?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Major activities include humane methods of slaughter inspections and enforcement

**Judge Reasoning**: The answer correctly states the appropriation amount, enabling acts, and major activities except for humane slaughter enforcement, which is a required fact. No prohibited errors or structural violations, but the omission of a key activity reduces completeness.

### direct_3 (score: 10)

**Question**: What amount is appropriated for NASA Science in FY2026, and what is the funding available for?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present and accurately stated. No prohibited errors are triggered; the answer focuses solely on NASA Science within the CJS context. The structure leads with the appropriation amount and lists allowed uses as categories without dollar breakdowns, fully complying with the mode-specific rules.

### direct_4 (score: 6)

**Question**: What amount is appropriated for the EPA Environmental Programs and Management account in FY2026, and what does that acco
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- EPA Environmental Programs and Management is appropriated $3,114,671,000
- The account supports necessary expenses for personnel, travel, passenger motor vehicles, aircraft, reprints, library memberships, and administrative costs
- Major set-asides include Geographic Programs $690,202,000

**Judge Reasoning**: The answer includes the main appropriation amount and many allowed uses, but omits 'EPA', general administrative costs, and the Geographic Programs set-aside ($690,202,000), which are significant gaps. No prohibited errors were triggered, and the structure follows the mode rules.

### direct_5 (score: 6)

**Question**: What amount is appropriated for VA Medical Services in FY2026, and what kinds of care or services does it cover?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Covered services include priority medical treatment and basic medical benefits for veterans in priority groups 1 through 6
- Covered services include prescription drugs, prosthetics, women veterans care, suicide prevention, caregiver support, PTSD services, rural health care, homelessness programs, telehealth, opioid prevention and treatment, and intimate partner violence assistance

**Judge Reasoning**: The answer correctly states the main appropriation amount and format, but misses critical required facts about priority groups 1-6 and the detailed list of covered services. No prohibited errors or structural violations, but significant factual gaps reduce the score.

### broad_1 (score: 9)

**Question**: What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- EPA includes $35,000,000 for U.S.-Mexico border water and wastewater facilities

**Judge Reasoning**: The answer correctly captures nearly all required funding details, properly groups by agency/account, and avoids prohibited additions. However, it omits the $35 million U.S.-Mexico border water/wastewater facilities figure, preventing a perfect score.

### broad_2 (score: 3)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Tenant-based rental assistance is appropriated $34,438,557,000
- Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025
- Tenant-based rental assistance includes $4,000,000,000 available October 1, 2026
- Tenant-based rental assistance includes $34,957,000,000 for renewals of expiring Section 8 tenant-based annual contributions contracts

**Structural Issues**:
- Missing tenant-based rental assistance entirely, which is a major funding category for rental assistance
- National homeless data analysis project ($10M) is misplaced under Youth homelessness instead of being nested under Homeless Assistance Grants
- No clear grouping by rental assistance vs. homelessness, just a flat list of accounts

**Judge Reasoning**: The answer covers homelessness and project-based rental assistance well but completely omits tenant-based rental assistance, a critical rental assistance funding stream. This major gap, along with structural placement issues, significantly reduces the score.

### broad_3 (score: 6)

**Question**: What FY2026 funding is available for airport infrastructure, runway improvements, or terminal upgrades?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- $542,356,000 is for Community Project Funding or Congressionally Directed Spending for airport projects
- $542,356,000 and $35,000,000 are suballocations within the $577,356,000 airport-grants heading

**Structural Issues**:
- The $35M discretionary grants are presented as a top-level item instead of being nested under the $577M Additional Grants-In-Aid. The $542M Community Project Funding suballocation is omitted entirely, further breaking nesting.

**Judge Reasoning**: The answer identifies the main airport buckets and avoids false totals, but omits the critical $542M suballocation and fails to nest the $35M discretionary portion under its parent, making the presentation incomplete and slightly misleading.

### broad_4 (score: 6)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- COPS includes $32,000,000 for Tribal law enforcement hiring and activities
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- Funding not properly nested: $84,000,000 for police-community relations and $50,000,000 for community violence intervention are presented as a separate bullet ('Initiatives to improve police-community relations') rather than as subprograms under the COPS total of $800,000,000.
- Missing required COPS subprogram: $32,000,000 for Tribal law enforcement hiring and activities is omitted.
- Missing targeted grants: $5,000,000 for cybercrimes against individuals and $7,500,000 for Daniel Anderl Judicial Security Act.

**Judge Reasoning**: Most required facts are present and no prohibited errors are triggered. However, significant omissions include the $32M Tribal COPS subprogram and the two targeted grants ($5M cybercrimes, $7.5M Anderl), and the structural presentation fails to nest the $84M and $50M initiatives under COPS, violating the parent-child relationship rule.

### broad_5 (score: 4)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 104(k) brownfields grants are $98,000,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Triggered Errors**:
- Should not omit Hazardous Substance Superfund or brownfields grants: brownfields grants (CERCLA section 104(k) $98M) are omitted

**Judge Reasoning**: The answer correctly identifies no clean total and lists major accounts like Superfund and LUST, but misses critical facts: the $98M brownfields grants, the $64.583M LUST cleanup sub-amount, and the fee authority note. This omission triggers a prohibited error (brownfields grants omitted), and overall fact coverage is incomplete, justifying a low score despite good structure.

### mechanism_1 (score: 10)

**Question**: How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly identifies the funding mechanism as continuing appropriations with rate-for-operations, references the extension through February 13, 2026, and explicitly states no full-year amount is provided. All required facts are covered, no errors triggered, and the structure is compact and explanatory.

### mechanism_2 (score: 10)

**Question**: What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately describes the Act as a continuing resolution that extends funding, changes an expiration date, and uses rate-for-operations based on FY2025 acts. It explicitly states no dollar amount was found, avoids all prohibited errors, and follows the structural rules. All required facts are present.

### mechanism_3 (score: 10)

**Question**: How does FY2026 handle FEMA Disaster Relief Fund funding under continuing appropriations?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly states no explicit dollar total was found, explains the CR mechanism, includes all required facts about extension, apportionment, rate-for-operations framework, and preservation of designations. No prohibited errors are triggered, and the structure is compact and compliant.

### mechanism_4 (score: 8)

**Question**: Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations mechanism?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions

**Judge Reasoning**: The answer correctly states no specific CISA dollar amount and describes the continuing resolution mechanism, including rate-for-operations and the extension to February 13, 2026. It omits the explicit explanation that a dollar total would need a separate line-item or baseline, but otherwise satisfies all requirements. No prohibited errors and structure is compliant.

### mechanism_5 (score: 7)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The continuation applies to continuing projects and activities through the date specified in section 106(3)
- They may continue only at the most limited funding action permitted
- Payments and reimbursements are made only to the extent and in the amounts provided in advance in appropriations Acts

**Judge Reasoning**: The answer correctly explains the CR mechanism, FY2025 rate, authority, and key payments, but misses three required details: the specific date reference to section 106(3), the 'most limited funding action' concept, and the condition that payments are made only to the extent and in amounts provided in advance. No prohibited errors, and structure follows mode rules.

### recon_1 (score: 10)

**Question**: Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what sho
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly breaks down FDA Salaries and Expenses into programmatic and financing-source dimensions, places all suballocations, caps, and transfers in the Not Added Separately section, and explicitly states that user fees are included in the total. All required facts are present, no prohibited errors are triggered, and the structure follows mode-specific rules perfectly.

### recon_2 (score: 8)

**Question**: Break down NASA FY2026 funding by major account, and explain which amounts can be summed versus which are suballocations
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- CECR prior-year project use is limited to not more than 20 percent or $50,000,000, whichever is less

**Structural Issues**:
- Lease proceeds cap and STEM joint funding contributions are placed in 'Included' under Financing-source breakdown, but they are caps/transfer limits and should be in 'Not Added Separately' per mode rules

**Judge Reasoning**: Nearly all required facts are present except the full condition of the CECR prior-year limitation. No prohibited errors are triggered. A minor structural issue exists with the placement of caps and financing limits in the Included section, but the answer clearly explains their non-additive nature.

### recon_3 (score: 5)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Direct and guaranteed loan authority total $1,065,000,000
- The two explicitly listed TA/circuit-rider lines total $58,900,000: $35,000,000 rural water and waste technical assistance grants plus $23,900,000 circuit rider
- $1,000,000 is for rural utilities program under section 306(a)(2)(B)
- $7,000,000 is for section 306A(i)(2) grants
- $60,000,000 is for loans and grants including water and waste disposal systems grants and Native/tribal/Hawaiian Home Lands purposes
- $4,000,000 is for solid waste management grants

**Structural Issues**:
- 0.25% management/oversight cap not placed in 'Not Added Separately' section; instead in 'Caveats'

**Judge Reasoning**: Answer correctly identifies major loan authority and subsidy/grant amounts and avoids prohibited errors, but fails to include several required line items (e.g., $7M, $60M, $4M, $1M 306(a)(2)(B)) and summary totals ($1,065B loans, $58.9M TA). The 0.25% cap is not placed in Not Added Separately as required.

### recon_4 (score: 4)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- The answer should not provide a derived water-infrastructure subtotal unless it lists the exact source-backed components included in that subtotal
- Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000
- STAG includes Save Our Seas section 302(a) grants of $3,500,000
- The STAG account includes non-water items outside this breakdown

**Triggered Errors**:
- Should not double-count project-specific amounts that are within the same broader STAG structure: Included section lists both SRF capitalization grants and project-specific CWSRF/DWSRF infrastructure amounts, e.g., CWSRF project-specific infrastructure: $892,762,272
- Should not present STAG's full $4,409,609,000 as entirely water infrastructure: Bottom line: $4,409,609,000 in STAG water-infrastructure funding is identified here.
- Should not assert a derived STAG water subtotal unless the listed components reconcile to it: The bottom line claims a water-infrastructure subtotal that does not reconcile with the listed components and equals the full STAG account total

**Structural Issues**:
- Double counting: parent totals (SRF capitalization grants) and suballocations (project-specific CWSRF/DWSRF) both appear in Included section.
- Derived water subtotal presented without reconciled components.

**Judge Reasoning**: The answer omits required facts (1459A(a)-(j) and Save Our Seas 302(a)), double-counts project-specific amounts, incorrectly labels the full STAG total as water infrastructure, and asserts an unreconciled water subtotal. Structural rules are violated. Major gaps and errors.

### recon_5 (score: 10)

**Question**: Break down IRS FY2026 funding by taxpayer services, enforcement, operations support, and business systems modernization,
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly lists the three main IRS accounts with exact amounts, identifies the missing BSM figure, and places all suballocations in the Not Added Separately section to avoid double counting, perfectly following the reconciliation breakdown structure.

### summary_1 (score: 5)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: The answer covers key funding and restriction facts but omits two required facts: the obligation plan requirement and the full list of user-fee sources. It avoids all prohibited errors and adheres to structural rules.

### summary_2 (score: 6)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water activities include Bureau of Reclamation and water storage or restoration projects
- Supported water activities include regulatory program activities for navigable waters and wetlands
- Supported cleanup/emergency activities include formerly utilized sites cleanup and flood control or coastal emergencies

**Judge Reasoning**: The answer is well-structured and covers many programs, but misses several required specifics: tribal energy, fossil energy R&D, Bureau of Reclamation, regulatory navigable waters/wetlands, and formerly utilized sites cleanup. No prohibited errors or structural issues.

### summary_3 (score: 10)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer covers all required facts across the three divisions, clearly distinguishes funding mechanisms without collapsing into a single total, avoids detailed dollar breakdowns, and adheres to all structural rules. No errors or omissions.

### summary_4 (score: 10)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately captures all required facts, avoids all prohibited errors, and follows the mode-specific structural rules perfectly. It clearly distinguishes regular and continuing appropriations using the CRX language, maintaining concise prose without extraneous formatting.

### summary_5 (score: 10)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer concisely summarizes THUD coverage for local governments, addressing both transportation and housing/urban development aspects with distinct programs and no prohibited errors. It follows all structural rules, making it a perfect evaluation.
