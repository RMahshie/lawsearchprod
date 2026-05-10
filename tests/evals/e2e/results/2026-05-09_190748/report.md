# E2E Eval Report

## Overall Summary

- **Questions**: 25 (25 scored)
- **Avg Score**: 7.1 / 10
- **Fact Recall**: 79.3%
- **Error Rate**: 7.8%
- **Classify Accuracy**: 88.0%
- **Route Accuracy**: 96.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 5 | 6.4 | 64.7% | 7.7% | 100.0% | 100.0% |
| direct_account_amount | 5 | 8.2 | 85.7% | 9.5% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 5 | 8.6 | 84.0% | 0.0% | 40.0% | 100.0% |
| general_summary | 5 | 4.2 | 42.3% | 14.3% | 100.0% | 80.0% |
| reconciliation_breakdown | 5 | 8.2 | 94.7% | 7.4% | 100.0% | 100.0% |

## Per-Question Detail

### direct_1 (score: 7)

**Question**: What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- User fees are credited to the account, including prescription drug, medical device, human generic drug, biosimilar, animal drug, generic new animal drug, and tobacco product user fees

**Triggered Errors**:
- Should not use internal pipeline language like extracted facts, retrieved facts, mapped facts, or source chunks: [[num:src_ag_cee4dfd9_de7e_40f0_b82e_f896328a8490_1]]

**Judge Reasoning**: The answer correctly provides the appropriation amount and names all major allowed uses, but fails to list the specific user fee types as required, and includes an internal citation token violating the prohibited error. These issues reduce the score, though the core answer is largely accurate.

### direct_2 (score: 10)

**Question**: What amount is provided for the USDA Food Safety and Inspection Service in FY2026, and what activities does it fund?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer leads with the main appropriation, lists authorizing statutes and major activities, correctly handles the representation allowance cap and fee crediting, follows the direct_account_amount mode without unnecessary detail, and contains all required facts with no prohibited errors.

### direct_3 (score: 10)

**Question**: What amount is appropriated for NASA Science in FY2026, and what is the funding available for?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer contains all required facts, commits no prohibited errors, and follows all mode-specific structural rules perfectly.

### direct_4 (score: 7)

**Question**: What amount is appropriated for the EPA Environmental Programs and Management account in FY2026, and what does that acco
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Major set-asides include Geographic Programs $690,202,000

**Judge Reasoning**: The answer correctly states the appropriation amount and availability, covers most required uses, and avoids prohibited errors. However, it omits the required fact about Geographic Programs set-aside and its $690,202,000 amount, making it incomplete. Structure and mode comply fully.

### direct_5 (score: 7)

**Question**: What amount is appropriated for VA Medical Services in FY2026, and what kinds of care or services does it cover?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Covered services include priority medical treatment and basic medical benefits for veterans in priority groups 1 through 6

**Triggered Errors**:
- Should not use internal language like extracted facts in the final answer: [[num:src_mcva_08c9a69c_0df6_4857_9061_9c15f3e960f6_1]]

**Judge Reasoning**: The answer correctly provides the $59.858 billion appropriation, mentions reimbursements, and lists the covered services comprehensively, but omits the required fact about priority groups 1-6. It also contains internal citation markers, flagged as an error. Most facts are present, no other errors.

### broad_1 (score: 6)

**Question**: What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- EPA State and Tribal Assistance Grants include Clean Water SRF capitalization grants of $1,638,861,000
- EPA State and Tribal Assistance Grants include Drinking Water SRF capitalization grants of $1,126,101,000

**Judge Reasoning**: The answer correctly identifies USDA RUS and EPA as controlling agencies, provides most key funding amounts with proper financial type labels, and adheres to structural rules. However, it fails to include the large EPA State and Tribal Assistance Grants capitalization grants for Clean Water and Drinking Water SRFs ($1.6B and $1.1B), which are major funding sources for rural water infrastructure. This omission reduces the score to 6.

### broad_2 (score: 4)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- THUD provides separate FY2026 funding streams for rental assistance and homelessness services
- Tenant-based rental assistance is appropriated $34,438,557,000
- Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025
- Tenant-based rental assistance includes $4,000,000,000 available October 1, 2026
- Tenant-based rental assistance includes $34,957,000,000 for renewals of expiring Section 8 tenant-based annual contributions contracts
- Project-based rental assistance is provided $18,143,000,000
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis
- Homelessness services include $107,000,000 for youth homelessness demonstration projects
- Youth homelessness system improvement grants may receive up to $25,000,000
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Triggered Errors**:
- Should not omit homelessness services when the question asks affordable housing, rental assistance, or homelessness services: Answer omits tenant-based and project-based rental assistance, which are key rental assistance funding streams.

**Judge Reasoning**: The answer covers Homeless Assistance Grants and Section 811 partially, but misses the vast majority of rental assistance programs (tenant-based and project-based) and other homelessness services like youth homelessness and data analysis, violating the prohibition on omitting key programs.

### broad_3 (score: 10)

**Question**: What FY2026 funding is available for airport infrastructure, runway improvements, or terminal upgrades?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts, avoids all prohibited errors, and follows the structural rules by nesting suballocations and clarifying that no clean total exists. The response is accurate and well-organized.

### broad_4 (score: 8)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- COPS includes $32,000,000 for Tribal law enforcement hiring and activities
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Judge Reasoning**: Answer covers most required facts, including all major COPS and OJP/JAG totals and key subprograms. It correctly nests suballocations and avoids prohibited errors. However, it omits COPS Tribal law enforcement hiring ($32M) and the Daniel Anderl grant ($7.5M), and does not label financial types.

### broad_5 (score: 4)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 104(k) brownfields grants are $98,000,000
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Triggered Errors**:
- Should not omit Hazardous Substance Superfund or brownfields grants: Brownfields grants (CERCLA section 104(k)) are omitted; only brownfields administrative costs are mentioned within Environmental Programs and Management.

**Judge Reasoning**: The answer correctly identifies the absence of a single cleanup total and provides Superfund and EPM amounts, but misses several required facts: brownfields grants ($98M), Superfund-related activities ($77.1M), Leaking Underground Storage Tank funding, and fee authority. It also violates the prohibition against omitting brownfields grants, leading to significant gaps.

### mechanism_1 (score: 10)

**Question**: How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?
**Answer Mode**: expected=funding_mechanism_no_amount actual=broad_topic_total MISMATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately describes DHS funding as a continuing resolution at FY2025 rates extended through February 13, 2026, and explicitly states no full-year amount exists. All required facts are present, no prohibited errors are triggered, and the qualitative nature of the response avoids any structural violations.

### mechanism_2 (score: 10)

**Question**: What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?
**Answer Mode**: expected=funding_mechanism_no_amount actual=general_summary MISMATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly identifies the Act's purpose of extending continuing appropriations, notes the expiration date change, clarifies it's a CR not a full-year bill, and describes the rate-for-operations mechanism. It avoids all prohibited errors and follows the concise prose structure perfectly.

### mechanism_3 (score: 8)

**Question**: How does FY2026 handle FEMA Disaster Relief Fund funding under continuing appropriations?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The continuing appropriations period is extended to February 13, 2026

**Judge Reasoning**: The answer correctly identifies the funding mechanism, avoids any dollar amounts, and follows the structural rules. However, it omits the specific extension date to February 13, 2026, which is a required fact.

### mechanism_4 (score: 9)

**Question**: Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations mechanism?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions

**Judge Reasoning**: The answer correctly states only a continuing-appropriations mechanism, no specific CISA dollar amount, and provides accurate mechanism details. It misses one required fact about what would be needed for a dollar total, but no errors and compact structure.

### mechanism_5 (score: 6)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=general_summary MISMATCH
**Route**: MATCH

**Missed Facts**:
- The Act allows certain payments and obligations to continue, including personnel pay and benefits, mandatory payments, essential activities to protect life and property, and orderly termination of government functions
- Payments and reimbursements are made only to the extent and in the amounts provided in advance in appropriations Acts

**Judge Reasoning**: The answer correctly covers continuation at FY2025 rate/authority, use of minimal funding, and the CR's end date. However, it omits required facts: it fails to list all allowed payment types (only mentions personnel pay) and does not state that payments are limited to prior appropriations. These gaps reduce completeness, justifying a score of 6.

### recon_1 (score: 10)

**Question**: Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what sho
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts, avoids all prohibited errors, and perfectly follows the reconciliation_breakdown structure with clear Included and Not Added Separately sections. No double counting or misclassifications occur.

### recon_2 (score: 9)

**Question**: Break down NASA FY2026 funding by major account, and explain which amounts can be summed versus which are suballocations
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- CECR prior-year project use is limited to not more than 20 percent or $50,000,000, whichever is less

**Judge Reasoning**: The answer correctly lists all NASA major accounts and correctly handles suballocations, transfers, and caps in the 'Not Added Separately' section. The only shortcoming is the incomplete description of the CECR prior-year limitation (lacking the 20% condition). No prohibited errors are triggered, and structure is perfect.

### recon_3 (score: 6)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Direct and guaranteed loan authority total $1,065,000,000
- The two explicitly listed TA/circuit-rider lines total $58,900,000: $35,000,000 rural water and waste technical assistance grants plus $23,900,000 circuit rider

**Triggered Errors**:
- Should not add $3,876,000 on top of the $51,476,000 parent line: $3,876,000 appears under Included > Financing-source breakdown alongside parent $51,476,000
- Should not add $110,488,564 on top of the $250,488,564 grant line: $110,488,564 appears under Included > Financing-source breakdown alongside parent $250,488,564

**Structural Issues**:
- Double counting: suballocations $3,876,000 and $110,488,564 appear in Included section alongside their parent totals, violating the no-double-counting rule.
- The $5,000,000 section 306E line and its subgrants $1,000,000 both appear in Included, creating another double-counting instance.

**Judge Reasoning**: The answer captures nearly all required individual facts but misses two explicit totals (loan authority sum and TA sum). It commits prohibited errors by listing suballocations within the Included section, causing double counting, and thus fails structural checks. Overall, a moderate score with significant structural issues.

### recon_4 (score: 6)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000
- STAG includes Save Our Seas section 302(a) grants of $3,500,000

**Structural Issues**:
- Parent totals (SRF capitalization grants) and their suballocations (project-specific suballocations) both appear in the Included section, violating the rule that they should not both appear in Included.

**Judge Reasoning**: The answer correctly lists most water infrastructure items but omits two grant programs (SDWA 1459A(a)-(j) of $28.5M and Save Our Seas 302(a) of $3.5M). It also violates the structural rule by including both parent SRF totals and their suballocations in the Included section. No prohibited errors were committed, and the STAG total is properly contextualized.

### recon_5 (score: 10)

**Question**: Break down IRS FY2026 funding by taxpayer services, enforcement, operations support, and business systems modernization,
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present, no prohibited errors were triggered, and the answer correctly uses Included/Not Added Separately sections to preserve parent-child math. The answer acknowledges the lack of a parent total and the absence of a Business Systems Modernization amount, fully meeting the reconciliation_breakdown mode requirements.

### summary_1 (score: 4)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment
- The division bars use of funds to implement electronic distribution of prescribing information for certain drugs unless federal law authorizes it

**Triggered Errors**:
- Should not omit the electronic prescribing-information restriction: no mention of electronic prescribing information restriction; instead mentions sodium reduction restriction

**Judge Reasoning**: The answer includes the funding for FDA salaries and expenses but misses required facts about the obligation plan and electronic prescribing restriction, while also failing to fully list all required user fee types. It also omits the prohibited error of the electronic prescribing restriction, leading to significant gaps. The structure is acceptable but content is incomplete.

### summary_2 (score: 6)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water activities include regulatory program activities for navigable waters and wetlands
- Supported cleanup/emergency activities include formerly utilized sites cleanup and flood control or coastal emergencies

**Judge Reasoning**: The answer covers many required facts about DOE energy programs and water activities but misses several specifics: power administration facilities, navigable waters and wetlands regulatory programs, formerly utilized sites cleanup, and flood control/coastal emergencies. No prohibited errors or structural issues. The omission of key water-related regulatory and cleanup details reduces completeness, warranting a score of 6.

### summary_3 (score: 6)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA

**Triggered Errors**:
- Should not provide a detailed dollar-by-dollar breakdown: Includes many specific dollar amounts such as $1,015,000,000, $50,000,000, $445,864,564, $35,000,000, $23,900,000, etc.

**Structural Issues**:
- Provides many specific dollar figures when only a few are needed to explain, violating the 'dollar figures only when they directly explain the answer' rule.

**Judge Reasoning**: The answer covers all three divisions and correctly notes separate funding mechanisms, but it provides a detailed dollar breakdown (violating the summary instruction) and omits key EPA programs like STAG, border, and Alaska infrastructure, resulting in a somewhat incomplete and overly detailed summary.

### summary_4 (score: 0)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MISMATCH
  - Expected: ['CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS']
  - Actual: []

**Missed Facts**:
- Regular appropriations provide full-year funding for specified accounts and programs
- Continuing appropriations temporarily extend funding for agencies or accounts without full-year appropriations
- Continuing appropriations generally operate at a prior-year rate for operations
- Continuing appropriations preserve prior-law authority and conditions for continuing projects and activities
- A continuing resolution is not the same as a new full-year line-item appropriation

**Triggered Errors**:
- Should not omit rate-for-operations concept: The answer does not mention the rate-for-operations concept.

**Judge Reasoning**: The answer is a complete refusal to address the question, providing none of the required facts and triggering the prohibited error of omitting the rate-for-operations concept. It is essentially empty of relevant content.

### summary_5 (score: 5)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs
- The division contains distinct accounts and programs rather than one single local-government funding pool

**Judge Reasoning**: The answer summarizes THUD coverage for local governments but omits key transportation programs (airport grants, transit, safety) and HUD programs (rental assistance, public housing, community programs). It does not mention the distinct account structure. It adheres to mode-specific rules and has no prohibited errors, resulting in significant gaps.
