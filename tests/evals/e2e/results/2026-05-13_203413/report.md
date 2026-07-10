# E2E Eval Report

## Overall Summary

- **Questions**: 25 (25 scored)
- **Avg Score**: 7.7 / 10
- **Fact Recall**: 76.5%
- **Error Rate**: 1.7%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 5 | 7.6 | 82.4% | 3.8% | 100.0% | 100.0% |
| direct_account_amount | 5 | 7.4 | 71.4% | 0.0% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 5 | 9.0 | 88.0% | 0.0% | 100.0% | 100.0% |
| general_summary | 5 | 7.8 | 76.9% | 0.0% | 100.0% | 100.0% |
| reconciliation_breakdown | 5 | 6.6 | 71.3% | 3.7% | 100.0% | 100.0% |

## Per-Question Detail

### direct_1 (score: 9)

**Question**: What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly provides the appropriation amount and all required major use categories and user fee information. It follows the mode's structural rules. The inclusion of minor administrative expense details (vehicle purchase, space rental, $25,000 limit) does not constitute an error but slightly exceeds the requested focus on major uses, preventing a perfect score.

### direct_2 (score: 5)

**Question**: What amount is provided for the USDA Food Safety and Inspection Service in FY2026, and what activities does it fund?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Major activities include inspection and enforcement for meat, poultry, and egg products
- Major activities include humane methods of slaughter inspections and enforcement

**Structural Issues**:
- Major allowed uses not explicitly named as categories; missing explicit listing of inspection and enforcement for meat, poultry, and egg products and humane methods of slaughter inspections and enforcement.

**Judge Reasoning**: The answer correctly provides the appropriation and references the relevant acts, but fails to explicitly mention the major activities of inspection/enforcement and humane slaughter inspections, which were required facts. No prohibited errors were triggered, but the structural rule requiring major activities to be named as categories was violated.

### direct_3 (score: 10)

**Question**: What amount is appropriated for NASA Science in FY2026, and what is the funding available for?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer perfectly matches all required facts, avoids all prohibited errors, and adheres to the direct_account_amount structural rules by leading with the appropriation amount, stating the purpose, and avoiding unnecessary breakdowns.

### direct_4 (score: 7)

**Question**: What amount is appropriated for the EPA Environmental Programs and Management account in FY2026, and what does that acco
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The account supports necessary expenses for personnel, travel, passenger motor vehicles, aircraft, reprints, library memberships, and administrative costs
- Major set-asides include Geographic Programs $690,202,000

**Judge Reasoning**: The answer correctly states the appropriation amount and lists most major uses, but omits the Geographic Programs set-aside, which is a required fact. No prohibited errors and structural rules are followed.

### direct_5 (score: 6)

**Question**: What amount is appropriated for VA Medical Services in FY2026, and what kinds of care or services does it cover?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Covered services include priority medical treatment and basic medical benefits for veterans in priority groups 1 through 6
- Covered services include prescription drugs, prosthetics, women veterans care, suicide prevention, caregiver support, PTSD services, rural health care, homelessness programs, telehealth, opioid prevention and treatment, and intimate partner violence assistance

**Judge Reasoning**: The answer correctly provides the appropriation amount and reimbursement, and broadly describes medical services. However, it fails to include required facts about coverage for priority groups 1-6 and omits numerous specific services like prescription drugs, prosthetics, women veterans care, etc. No prohibited errors were triggered and structure is appropriate.

### broad_1 (score: 7)

**Question**: What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- EPA includes $35,000,000 for U.S.-Mexico border water and wastewater facilities

**Triggered Errors**:
- Should not omit EPA/Interior for rural water or wastewater infrastructure: No mention of Interior, Department of Interior, or Bureau of Reclamation; answer only mentions USDA and EPA.

**Judge Reasoning**: The answer correctly identifies the lack of a single total and groups funding by agency/account, covering most required facts and avoiding most prohibited errors. However, it omits the $35 million for U.S.-Mexico border water facilities and does not mention the Department of Interior, which are a missing fact and a prohibited error, respectively. Overall structure and labeling are strong.

### broad_2 (score: 7)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis
- Homelessness services include $107,000,000 for youth homelessness demonstration projects
- Youth homelessness system improvement grants may receive up to $25,000,000
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Judge Reasoning**: The answer correctly identifies the main rental assistance and homelessness accounts, provides accurate key amounts, and follows structural rules with nested suballocations and a non-additivity caveat. However, it misses several specific required facts: the $10M homeless data analysis, $107M youth homelessness demos, $25M youth improvement grants, and the $8.3B Public Housing Fund.

### broad_3 (score: 10)

**Question**: What FY2026 funding is available for airport infrastructure, runway improvements, or terminal upgrades?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Judge Reasoning**: The answer contains all required facts, avoids prohibited errors, and perfectly follows the mode-specific structural rules by grouping funding by account, not fabricating a summed total, labeling financial types, and nesting suballocations under their parent amount.

### broad_4 (score: 8)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- Police-community relations initiatives ($84M) and community violence intervention ($50M) are COPS sub-programs but are not nested under the COPS account. They appear as separate top-level buckets.

**Judge Reasoning**: The answer accurately presents the major OJP and COPS totals and sub-programs, avoids prohibited errors, and explicitly disclaims a single additive total. However, it omits two required targeted grant amounts (cybercrimes and Daniel Anderl) and fails to nest the $84M police-community relations bucket (and its $50M sub-component) under COPS, violating structural nesting rules.

### broad_5 (score: 6)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Judge Reasoning**: The answer correctly emphasizes separate accounts and avoids an improper total, and includes many key amounts. However, it omits the $77.1M for CERCLA sections 311(a) and 126(g), fails to mention the fee authority, and misstates the LUST amount as entirely for cleanup rather than the $64.6M subset, resulting in significant factual gaps.

### mechanism_1 (score: 10)

**Question**: How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts, commits no errors, and perfectly follows the compact bottom-line + mechanism bullets structure without hallucinated amounts or extraneous sections.

### mechanism_2 (score: 10)

**Question**: What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately includes all required facts, avoids all prohibited errors, and perfectly follows the mode-specific structural rules by explicitly stating no dollar total, explaining the funding mechanism via bullets, and remaining compact.

### mechanism_3 (score: 8)

**Question**: How does FY2026 handle FEMA Disaster Relief Fund funding under continuing appropriations?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Prior disaster-relief designations are preserved for amounts incorporated by reference

**Judge Reasoning**: The answer correctly identifies no explicit dollar amount, describes the CR mechanism, extension, apportionment, and reference to FY2025 acts. It misses only the preservation of prior disaster-relief designations, which is a minor gap. No errors and structure follows the mode's rules.

### mechanism_4 (score: 9)

**Question**: Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations mechanism?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions

**Judge Reasoning**: The answer directly states no specific CISA dollar amount and thoroughly explains the continuing-appropriations mechanism, including the extension date and rate-for-operations. It avoids all prohibited errors and follows structural rules. The only minor gap is the explicit mention that a dollar total would require a separate line-item appropriation, but this does not detract from the core accuracy.

### mechanism_5 (score: 8)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Payments and reimbursements are made only to the extent and in the amounts provided in advance in appropriations Acts

**Judge Reasoning**: The answer correctly conveys the CR mechanism, including rate, authority, conditions, and allowed payments, but omits the requirement that payments be made only to the extent and in amounts provided in advance. No prohibited errors or structural issues.

### recon_1 (score: 9)

**Question**: Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what sho
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- FY2027 user fees accepted in FY2026 are excluded from FY2026 amounts under this heading

**Judge Reasoning**: All required facts are present except the note about FY2027 user fees being excluded from FY2026 amounts. No prohibited errors were triggered. The structure perfectly follows mode-specific rules with clear Included/Not Added Separately sections and no double-counting.

### recon_2 (score: 9)

**Question**: Break down NASA FY2026 funding by major account, and explain which amounts can be summed versus which are suballocations
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- CECR prior-year project use is limited to not more than 20 percent or $50,000,000, whichever is less

**Judge Reasoning**: All major accounts and suballocation treatments are correct and clearly separated. The answer follows the reconciliation_breakdown structure perfectly. The only minor omission is the 20% alternative in the CECR prior-year project cap fact.

### recon_3 (score: 6)

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

**Judge Reasoning**: Answer correctly separates loan authority from cost funding and avoids all prohibited errors. Structure conforms to reconciliation mode with Included/Not Added Separately sections. However, several required dollar amounts and totals are missing (e.g., $1,065M total loan authority, $58.9M TA total, $7M grants, $60M loans/grants, $4M solid waste, $1M 306(a)(2)(B)), which reduces completeness.

### recon_4 (score: 2)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Clean Water SRF capitalization grants are $1,638,861,000
- Drinking Water SRF capitalization grants are $1,126,101,000
- Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000
- Safe Drinking Water Act section 1464(d) grants are $28,000,000
- STAG includes section 1459B grants of $22,000,000
- STAG includes section 1459A(l) grants of $6,500,000
- STAG includes FWPCA section 104(b)(8) grants of $25,500,000
- STAG includes FWPCA section 221 grants of $41,000,000
- STAG includes America's Water Infrastructure Act section 4304(b) grants of $5,400,000
- STAG includes Save Our Seas section 302(a) grants of $3,500,000
- STAG includes CPF/CDS remediation, construction, and environmental management projects of $20,364,000
- U.S.-Mexico Border high-priority water and wastewater facilities are $35,000,000
- Alaska rural and Alaska Native Village drinking water and wastewater infrastructure needs are $39,000,000
- SRF and project-specific amounts sit within the broader STAG account structure
- The STAG account includes non-water items outside this breakdown

**Triggered Errors**:
- Should not omit either Clean Water SRF or Drinking Water SRF: The answer provides no distinct Drinking Water SRF capitalization grant total; only a single SRF line of $1,638,861,000 is given, which corresponds to Clean Water, and the Drinking Water SRF total of $1,126,101,000 is omitted.

**Structural Issues**:
- Parent totals and suballocations both appear in Included: the SRF capitalization grant ($1,638,861,000) is listed in Included alongside its suballocations (Clean Water project-specific $892,762,272 and Drinking Water project-specific $715,364,627), which violates the 'no double counting' rule for Included items.

**Judge Reasoning**: The answer misses the vast majority of required water infrastructure grant line items listed in the gold reference, omits the Drinking Water SRF capitalization grant total, and violates structural rules by placing suballocations in the Included section. Significant gaps and errors result in a low score.

### recon_5 (score: 7)

**Question**: Break down IRS FY2026 funding by taxpayer services, enforcement, operations support, and business systems modernization,
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- $275,000,000 remains available within Technology and Operations Support and is not added on top
- $10,000,000 is within Technology and Operations Support for equipment and facilities acquisition
- $1,000,000 is within Technology and Operations Support for research
- $20,000 is within Technology and Operations Support for official reception and representation expenses

**Judge Reasoning**: The answer correctly breaks down IRS taxpayer services, enforcement, and technology operations support amounts, and properly notes no separate BSM amount. It organizes suballocations under Not Added Separately, avoiding double counting. However, it omits several required Technology and Operations Support suballocations ($275M, $10M, $1M, $20K), reducing completeness.

### summary_1 (score: 5)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: The answer captures the core funding and the prescribing information restriction but omits the user fee support details and the obligation plan requirement. No prohibited errors were triggered, and the structure follows the mode rules. Missing two of four required facts results in a moderate score.

### summary_2 (score: 7)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water and civil works activities include hydroelectric facility operations and upgrades
- The division also funds administration and oversight, including Departmental Administration and the Office of Inspector General

**Judge Reasoning**: The answer broadly covers the division's activities in energy, nuclear, water, and regulation, but omits key specifics like hydroelectric facilities, tribal energy, fossil energy R&D, and explicit mention of Departmental Administration/OIG. Structure and prohibition rules are fully met.

### summary_3 (score: 8)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA

**Judge Reasoning**: The answer effectively summarizes water infrastructure treatment across all three agencies, highlights distinct funding mechanisms, and avoids prohibited errors. It narrowly misses a required EPA fact (STAG and Alaska not explicitly named) but overall remains accurate and well-structured.

### summary_4 (score: 10)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer clearly distinguishes regular and continuing appropriations, includes all required facts, avoids prohibited errors, and follows the mode-specific structure with concise bullets and no unnecessary dollar amounts or sections.

### summary_5 (score: 9)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer thoroughly covers both transportation and HUD programs relevant to local governments with specific examples, clearly notes the multi-account structure, and avoids prohibited errors. It is structured as concise bullets with explanatory prose, though the numerous dollar figures make it slightly more detailed than a fully succinct summary.
