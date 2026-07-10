# E2E Eval Report

## Overall Summary

- **Questions**: 25 (25 scored)
- **Avg Score**: 7.4 / 10
- **Fact Recall**: 78.3%
- **Error Rate**: 2.6%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 5 | 4.6 | 60.8% | 11.5% | 100.0% | 100.0% |
| direct_account_amount | 5 | 8.4 | 81.0% | 0.0% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 5 | 9.6 | 96.0% | 0.0% | 100.0% | 100.0% |
| general_summary | 5 | 6.8 | 53.8% | 0.0% | 100.0% | 100.0% |
| reconciliation_breakdown | 5 | 7.6 | 89.4% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### direct_1 (score: 8)

**Question**: What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- User fees are credited to the account, including prescription drug, medical device, human generic drug, biosimilar, animal drug, generic new animal drug, and tobacco product user fees

**Judge Reasoning**: The answer correctly states the appropriation amount and covers all major allowed use categories. However, it omits the specific types of user fees that are credited to the account, which is a required fact in the gold reference. No prohibited errors or structural issues were found.

### direct_2 (score: 10)

**Question**: What amount is provided for the USDA Food Safety and Inspection Service in FY2026, and what activities does it fund?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts, commits no prohibited errors, and perfectly follows the mode-specific structural rules by leading with the main amount and naming major activity categories.

### direct_3 (score: 10)

**Question**: What amount is appropriated for NASA Science in FY2026, and what is the funding available for?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer contains all required facts, avoids prohibited errors, and follows structural rules by leading with the appropriation amount and describing the purpose categorically. It is a perfect answer for the direct_account_amount mode.

### direct_4 (score: 6)

**Question**: What amount is appropriated for the EPA Environmental Programs and Management account in FY2026, and what does that acco
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The funding remains available until September 30, 2027
- Major set-asides include Geographic Programs $690,202,000

**Structural Issues**:
- The answer omitted a major allowed use category: Geographic Programs set-aside ($690,202,000), which should have been listed as required by the gold reference and mode-specific rules.

**Judge Reasoning**: The answer correctly states the appropriation amount and most major uses, but fails to include the availability date (until September 30, 2027) and the significant Geographic Programs set-aside ($690,202,000). No prohibited errors are triggered, and the structure mostly follows the direct account amount mode, except for the omission. The missing facts lower the score.

### direct_5 (score: 8)

**Question**: What amount is appropriated for VA Medical Services in FY2026, and what kinds of care or services does it cover?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Covered services include priority medical treatment and basic medical benefits for veterans in priority groups 1 through 6

**Judge Reasoning**: The answer correctly states the appropriation amount and covers most required services, but it fails to mention priority medical treatment for priority groups 1-6, a key required fact. No prohibited errors or structural issues are present.

### broad_1 (score: 6)

**Question**: What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- EPA includes $35,000,000 for U.S.-Mexico border water and wastewater facilities
- EWD includes a Northwestern New Mexico Rural Water Projects Act authorization increase from $870,000,000 to $1,815,000,000, but it is not a clean FY2026 appropriation

**Triggered Errors**:
- Should not omit EPA/Interior for rural water or wastewater infrastructure: no mention of Interior or EWD authority

**Judge Reasoning**: The answer correctly identifies key accounts and amounts, adheres to structural rules, and avoids mixing financial types. However, it omits two required facts (U.S.-Mexico border $35M and Northwestern New Mexico authorization increase) and triggers a prohibited error by completely leaving out Interior Department funding.

### broad_2 (score: 3)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Tenant-based rental assistance is appropriated $34,438,557,000
- Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025
- Tenant-based rental assistance includes $4,000,000,000 available October 1, 2026
- Tenant-based rental assistance includes $34,957,000,000 for renewals of expiring Section 8 tenant-based annual contributions contracts
- Project-based rental assistance is provided $18,143,000,000
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis
- Supportive housing for persons with disabilities includes $287,000,000 for Section 811 project rental assistance and associated supportive services

**Structural Issues**:
- Tenant-based rental assistance section lacks the parent appropriation total ($34.4B) and major components, making the nesting incomplete.
- Project-based rental assistance ($18.1B) is entirely absent.
- Funding types (appropriation, advance) are not consistently labeled; e.g., public housing fund sub-allocations lack type tags.

**Judge Reasoning**: The answer correctly identifies that no single total exists and provides accurate details on homelessness grants, but misses the entire tenant- and project-based rental assistance appropriations, which are critical to the question. This substantial factual gap warrants a low score.

### broad_3 (score: 5)

**Question**: What FY2026 funding is available for airport infrastructure, runway improvements, or terminal upgrades?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- $542,356,000 is for Community Project Funding or Congressionally Directed Spending for airport projects
- Up to $35,000,000 is for discretionary grants to airports for eligible projects
- $542,356,000 and $35,000,000 are suballocations within the $577,356,000 airport-grants heading

**Judge Reasoning**: The answer correctly identifies the main airport grant accounts and amounts, but omits key required facts about the suballocations within the $577M additional grants (Community Project Funding and discretionary grants). This leaves significant fact gaps, though no errors or structural violations are present.

### broad_4 (score: 4)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Local law enforcement, community violence prevention, and police hiring funding is primarily in OJP and COPS
- OJP is $2,400,000,000
- OJP includes $964,000,000 for the Edward Byrne Memorial JAG program
- COPS includes $32,000,000 for Tribal law enforcement hiring and activities
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Triggered Errors**:
- Should not omit either OJP/Byrne JAG or COPS hiring/community violence funding: OJP and Byrne JAG are entirely omitted

**Structural Issues**:
- Funding is not clearly grouped by agency/account; OJP is missing.
- The $84 million police-community relations and $50 million community violence intervention are not nested under COPS, violating 'suballocations should be nested under their parent account'.
- Amounts are not labeled with financial types (e.g., 'appropriation', 'grant').

**Judge Reasoning**: The answer covers COPS details well but completely omits OJP and Byrne JAG, and misses tribal hiring and cybercrime grants. It fails to properly nest suballocations and violates structural grouping rules, resulting in significant fact gaps and structural errors.

### broad_5 (score: 5)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 128 grants are $46,250,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Triggered Errors**:
- Should not omit Hazardous Substance Superfund or brownfields grants: Omits CERCLA section 128 grants ($46,250,000) and fee authority; brownfields grants are partially omitted.

**Judge Reasoning**: The answer correctly identifies no clean total and provides several key funding figures, but it omits CERCLA section 128 grants ($46.25M) and the brownfields fee authority note, and does not break out the LUST cleanup sub-amount. This triggers the prohibited error of omitting brownfields grants and results in significant fact gaps.

### mechanism_1 (score: 10)

**Question**: How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts about the continuing resolution mechanism, rate-for-operations, extension date, and absence of full-year amount. It commits no prohibited errors and follows the mode-specific structural rules perfectly.

### mechanism_2 (score: 10)

**Question**: What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts, avoids all prohibited errors, and perfectly follows the funding_mechanism_no_amount structural rules. It clearly states that no dollar total was found, explains the CR mechanism with rate-for-operations language, and uses a compact bottom-line plus bullets format under the correct routing.

### mechanism_3 (score: 10)

**Question**: How does FY2026 handle FEMA Disaster Relief Fund funding under continuing appropriations?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present with clear evidence, no prohibited errors are triggered, and the answer perfectly follows the compact, mechanism-focused structure without hallucinating any dollar amounts.

### mechanism_4 (score: 8)

**Question**: Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations mechanism?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions

**Judge Reasoning**: The answer clearly states no specific CISA amount is provided and explains the CR mechanism with FY2025 rate and extension date. It fails to explicitly mention that a dollar total would require a separate line-item not present, a minor omission among required facts. No errors and compact structure.

### mechanism_5 (score: 10)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present and accurately described, no prohibited errors are triggered, and the answer adheres perfectly to the mode-specific structural rules. It provides a compact explanation of the CR mechanism with clear bullet points.

### recon_1 (score: 10)

**Question**: Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what sho
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: The answer provides a complete breakdown of FDA Salaries and Expenses programmatic totals, financing sources, and correctly separates suballocations, caps, and transfers into 'Not Added Separately'. All required facts are present with no errors, and structural rules are followed perfectly.

### recon_2 (score: 6)

**Question**: Break down NASA FY2026 funding by major account, and explain which amounts can be summed versus which are suballocations
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- NASA major accounts include Space Technology $920,500,000
- NASA major accounts include Exploration $7,783,000,000

**Structural Issues**:
- Lease proceeds are mentioned both under 'Included' (Financing-source breakdown) and under 'Not Added Separately' (Financing-source treatment), causing redundancy and slightly blurring the section distinction.

**Judge Reasoning**: Most required facts are present and correctly handled, prohibited errors are avoided, and the answer generally follows the reconciliation structure. However, two major account lines (Space Technology $920.5M and Exploration $7,783M) are omitted, creating a significant gap in the programmatic breakdown. The answer acknowledges the conflicting excerpt but should have included the accounts with a note, as required. Minor structural redundancy with lease proceeds wording.

### recon_3 (score: 8)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Direct and guaranteed loan authority total $1,065,000,000
- The two explicitly listed TA/circuit-rider lines total $58,900,000: $35,000,000 rural water and waste technical assistance grants plus $23,900,000 circuit rider
- $1,000,000 is for rural utilities program under section 306(a)(2)(B)
- $5,000,000 is for section 306E rural utilities activity
- $1,000,000 within section 306E is for subgrants for household decentralized wastewater systems

**Judge Reasoning**: The answer includes most required facts, avoids all prohibited errors, and follows the structural rules. However, it omits explicit totals for loan authority ($1.065B) and TA/circuit-rider ($58.9M), and does not provide full section citations for the $1,000,000 and $5,000,000 rural utilities lines, nor the household wastewater subgrant detail. Overall, it accurately breaks down the account and clarifies non-additive items.

### recon_4 (score: 7)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000

**Judge Reasoning**: Most required facts are present and the answer correctly avoids double-counting and structural errors. However, it omits the SDWA section 1459A(a)-(j) grants of $28,500,000, a significant missing fact that prevents a perfect score.

### recon_5 (score: 7)

**Question**: Break down IRS FY2026 funding by taxpayer services, enforcement, operations support, and business systems modernization,
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Enforcement includes not more than $35,000,000 for Criminal Investigation investigative technology
- Transfer authority of up to 5 percent of IRS funds is a limitation on use, not a separate FY2026 funding amount

**Judge Reasoning**: Most required facts are present, but two are missing: the $35M limitation for Criminal Investigation investigative technology and the 5% transfer authority. No prohibited errors were triggered and structural rules are fully satisfied. The answer accurately captures the parent totals and suballocations without double counting.

### summary_1 (score: 6)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: The answer correctly captures FDA funding and key restrictions, including the electronic prescribing-information restriction, but misses required facts about specific user-fee types and the obligation plan requirement, leading to a slightly lower score.

### summary_2 (score: 4)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water and civil works activities include hydroelectric facility operations and upgrades
- Supported water activities include Bureau of Reclamation and water storage or restoration projects
- Supported water activities include regulatory program activities for navigable waters and wetlands
- Supported cleanup/emergency activities include formerly utilized sites cleanup and flood control or coastal emergencies
- The division also funds administration and oversight, including Departmental Administration and the Office of Inspector General

**Judge Reasoning**: The answer provides a broad overview but misses several required programs: fossil energy R&D, hydroelectric facilities, Bureau of Reclamation, navigable waters/wetlands regulation, formerly utilized sites cleanup, and specific oversight offices. No prohibited errors, structure is fine.

### summary_3 (score: 7)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- USDA supports rural water and waste disposal through Rural Utilities Service loans, guarantees, grants, and technical assistance
- Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material

**Judge Reasoning**: The answer correctly identifies the three agencies and their different funding mechanisms, and it does not total them. However, it omits Bureau of Reclamation for Energy-Water and technical assistance for USDA, leading to incomplete coverage of key facts.

### summary_4 (score: 10)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately contrasts regular and continuing appropriations with all required facts, avoids all prohibited errors, and adheres to the concise prose structural rules.

### summary_5 (score: 7)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs

**Judge Reasoning**: The answer provides a solid general summary of THUD for local governments, covering both transportation and housing programs with distinct accounts, but it omits specific transportation activities like airport grants and highway programs, and does not mention project-based rental assistance on the HUD side, which were required facts. The use of dollar amounts, while informative, makes it somewhat less concise.
