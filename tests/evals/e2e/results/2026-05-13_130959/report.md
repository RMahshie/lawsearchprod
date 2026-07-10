# E2E Eval Report

## Overall Summary

- **Questions**: 25 (25 scored)
- **Avg Score**: 8.0 / 10
- **Fact Recall**: 81.6%
- **Error Rate**: 0.9%
- **Classify Accuracy**: 96.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 5 | 7.0 | 68.6% | 3.8% | 100.0% | 100.0% |
| direct_account_amount | 5 | 8.6 | 85.7% | 0.0% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 5 | 9.0 | 84.0% | 0.0% | 80.0% | 100.0% |
| general_summary | 5 | 7.2 | 73.1% | 0.0% | 100.0% | 100.0% |
| reconciliation_breakdown | 5 | 8.0 | 89.4% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### direct_1 (score: 10)

**Question**: What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately states the appropriation amount, covers all required major uses in a compact categorical form, and correctly mentions user fees without dollar breakdowns, perfectly adhering to the mode-specific structural rules and containing no prohibited errors.

### direct_2 (score: 10)

**Question**: What amount is provided for the USDA Food Safety and Inspection Service in FY2026, and what activities does it fund?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer contains all required facts, makes no prohibited errors, and adheres perfectly to the mode-specific structural rules by leading with the appropriation amount and listing allowed uses as categories.

### direct_3 (score: 10)

**Question**: What amount is appropriated for NASA Science in FY2026, and what is the funding available for?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are explicitly present in the answer. No prohibited errors were triggered. The structural rules are fully satisfied: the answer leads with the appropriation amount, lists allowed uses as categories, and avoids any breakdown or extraneous sections.

### direct_4 (score: 8)

**Question**: What amount is appropriated for the EPA Environmental Programs and Management account in FY2026, and what does that acco
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Major set-asides include Geographic Programs $690,202,000

**Structural Issues**:
- Provided specific dollar amounts for set-asides (Energy Star, Grants, National Priorities) instead of only naming categories as directed.

**Judge Reasoning**: The answer includes almost all required facts, with the notable omission of the Geographic Programs set-aside amount. No prohibited errors are triggered. The structure is generally good but it provides dollar amounts for the listed set-asides, contrary to the guideline to name categories without dollar-by-dollar breakdown. This minor structural issue and the missing fact keep the score from a perfect 10.

### direct_5 (score: 5)

**Question**: What amount is appropriated for VA Medical Services in FY2026, and what kinds of care or services does it cover?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Covered services include priority medical treatment and basic medical benefits for veterans in priority groups 1 through 6
- Covered services include prescription drugs, prosthetics, women veterans care, suicide prevention, caregiver support, PTSD services, rural health care, homelessness programs, telehealth, opioid prevention and treatment, and intimate partner violence assistance

**Judge Reasoning**: The answer correctly states the amount and reimbursements but fails to mention priority groups and covers only caregiver support from the required list of services, missing many specific care categories. No errors or structural issues, but significant fact gaps reduce the score.

### broad_1 (score: 10)

**Question**: What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are accurately present with clear citations. No prohibited errors are triggered. The answer follows all structural rules: it groups by agency/account, avoids fabricated totals, labels amounts by financial type, and nests suballocations. Perfect adherence to the gold reference.

### broad_2 (score: 4)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Tenant-based rental assistance is appropriated $34,438,557,000
- Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025
- Tenant-based rental assistance includes $4,000,000,000 available October 1, 2026
- Tenant-based rental assistance includes $34,957,000,000 for renewals of expiring Section 8 tenant-based annual contributions contracts
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis
- Homelessness services include $107,000,000 for youth homelessness demonstration projects
- Youth homelessness system improvement grants may receive up to $25,000,000
- Supportive housing for persons with disabilities includes $287,000,000 for Section 811 project rental assistance and associated supportive services
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Structural Issues**:
- Amounts are not consistently labeled by financial type (e.g., appropriation, advance appropriation); some are just dollar figures without clear type.
- Grouping mixes accounts (e.g., Public housing with HOPWA) without clear hierarchy, though suballocations are nested for some entries.

**Judge Reasoning**: The answer correctly identifies the THUD context and avoids aggregating into a single total. It captures project-based rental assistance and homeless assistance grants with proper nesting, but omits all tenant-based rental assistance details (a major portion), youth homelessness, supportive housing, and homeless data analysis. Significant required facts are missing, though no prohibited errors are committed. Structural issues include insufficient financial type labeling. Overall, the answer has major factual gaps, warranting a low score.

### broad_3 (score: 10)

**Question**: What FY2026 funding is available for airport infrastructure, runway improvements, or terminal upgrades?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present with clear evidence, no prohibited errors are triggered, and the answer adheres perfectly to the mode-specific structural rules by grouping accounts, nesting suballocations, labeling financial types, and avoiding mixed-type totals.

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
- Should not omit either OJP/Byrne JAG or COPS hiring/community violence funding: OJP and Byrne JAG completely omitted

**Structural Issues**:
- Not grouped by agency/account; OJP missing entirely.
- COPS suballocations not clearly nested under the $800M parent; police-community relations bucket listed separately without explicit parent reminder.
- Other grants listed as flat buckets without agency context.

**Judge Reasoning**: The answer provides substantial detail on COPS accounts but completely omits OJP and the Byrne JAG program, which are major required facts. The structural presentation is flattened and fails to clearly nest suballocations or group by agency. Only partial credit for covering some COPS elements.

### broad_5 (score: 7)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Judge Reasoning**: The answer correctly separates accounts and avoids a summed total, includes all major cleanup-related lines, and adheres to structural rules. However, it omits the $64,583,000 cleanup suballocation within the LUST Trust Fund and does not mention the fee authority under CERCLA section 3024, resulting in a score of 7.

### mechanism_1 (score: 10)

**Question**: How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately states DHS funding is via continuing appropriations at the FY2025 rate, extended to February 13, 2026, with no full-year amount. It covers the mechanism, apportionment, and prior-law reference without hallucination, errors, or structural issues.

### mechanism_2 (score: 9)

**Question**: What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?
**Answer Mode**: expected=funding_mechanism_no_amount actual=general_summary MISMATCH
**Route**: MATCH

**Missed Facts**:
- It changes or extends the operative expiration date in the continuing appropriations framework

**Judge Reasoning**: The answer captures the essential nature and mechanism of the Further Continuing Appropriations Act accurately and avoids all prohibited errors. However, it fails to explicitly state that the Act changes or extends the operative expiration date of the continuing appropriations framework, which is a required fact. All other facts are present and structural rules followed.

### mechanism_3 (score: 7)

**Question**: How does FY2026 handle FEMA Disaster Relief Fund funding under continuing appropriations?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The continuing appropriations period is extended to February 13, 2026
- Prior disaster-relief designations are preserved for amounts incorporated by reference

**Judge Reasoning**: The answer correctly explains the CR mechanism and the absence of a dollar amount for DRF, but it misses the specific extension date and the preservation of prior designations. No prohibited errors were made, and the structure is mostly compact, though slightly incomplete.

### mechanism_4 (score: 9)

**Question**: Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations mechanism?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions

**Judge Reasoning**: The answer clearly states there is no specific dollar amount and explains the continuing-appropriations mechanism with the rate-for-operations basis and extension date. All prohibited errors are avoided, and the structure is compact and compliant. The only minor omission is not explicitly stating that a separate line-item appropriation would be required for a dollar total, but the core answer is fully sufficient.

### mechanism_5 (score: 10)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts, avoids prohibited errors, and follows the compact fundraising mechanism explanation structural rules. It correctly describes the continuing resolution's effect on agencies without full-year appropriations.

### recon_1 (score: 9)

**Question**: Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what sho
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- FY2027 user fees accepted in FY2026 are excluded from FY2026 amounts under this heading

**Judge Reasoning**: All required facts are present except the exclusion of FY2027 fees, which is not mentioned. No prohibited errors, and structural rules are perfectly followed. The answer clearly separates programmatic and financing breakdowns, with proper handling of suballocations and limitations.

### recon_2 (score: 6)

**Question**: Break down NASA FY2026 funding by major account, and explain which amounts can be summed versus which are suballocations
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- NASA major accounts include Space Technology $920,500,000
- NASA major accounts include Exploration $7,783,000,000
- $33,000,000 lease-proceeds availability cap is inside CECR and is not standalone budget authority
- CECR prior-year project use is limited to not more than 20 percent or $50,000,000, whichever is less

**Structural Issues**:
- Space Technology and Exploration are major accounts but are listed in 'Not Added Separately' instead of 'Included'.
- The $935,000,000 figure is listed in both 'Included' as Aeronautics and in 'Not Added Separately' with an ambiguous label as a 'NASA Science suballocation', causing potential double‑counting or misclassification.

**Judge Reasoning**: The answer correctly lists seven major accounts and properly isolates most suballocations, transfers, and limits. However, it misclassifies Space Technology and Exploration as non‑additive items instead of including them as major accounts, omits the $33M lease‑proceeds cap, and incompletely describes the CECR prior‑year limit, leading to factual gaps and structural inconsistencies.

### recon_3 (score: 8)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Direct and guaranteed loan authority total $1,065,000,000
- The two explicitly listed TA/circuit-rider lines total $58,900,000: $35,000,000 rural water and waste technical assistance grants plus $23,900,000 circuit rider
- 0.25 percent management/oversight retention is a cap or limitation

**Judge Reasoning**: The answer correctly identifies the breakdown and avoids all prohibited errors, with sound structure. It omits the 0.25% oversight retention cap and the explicit sums for total loan authority and TA total, which are required facts.

### recon_4 (score: 7)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000
- The STAG account includes non-water items outside this breakdown

**Judge Reasoning**: The answer correctly identifies the STAG total and major water infrastructure components, with clear warnings against double-counting SRF suballocations. However, it omits the Safe Drinking Water Act section 1459A(a)-(j) grants of $28,500,000, which is a required fact. It also does not explicitly note that the STAG account includes non-water items outside the breakdown. Structure is sound and no prohibited errors were triggered.

### recon_5 (score: 10)

**Question**: Break down IRS FY2026 funding by taxpayer services, enforcement, operations support, and business systems modernization,
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly presents the IRS funding breakdown with proper categorization into Included and Not Added Separately sections. All required facts are present, no prohibited errors are triggered, and the mode-specific structural rules are followed, resulting in a perfect score.

### summary_1 (score: 6)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: The answer correctly describes the Agriculture division's funding and includes the electronic prescribing restriction, but it omits the required obligation plan and fails to mention generic new animal drugs among the user fees. No prohibited errors and structure is concise and appropriate.

### summary_2 (score: 5)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water activities include regulatory program activities for navigable waters and wetlands
- Supported cleanup/emergency activities include formerly utilized sites cleanup and flood control or coastal emergencies

**Judge Reasoning**: The answer provides a solid high-level overview of EWD projects, covering water, energy, nuclear, and administration, with no prohibited errors and good structure. However, it omits three specific required facts: tribal energy and fossil energy R&D under DOE; regulatory program activities for navigable waters/wetlands; and formerly utilized sites cleanup. This creates significant fact gaps, meriting a score of 5.

### summary_3 (score: 7)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material

**Judge Reasoning**: The answer covers all required agencies and most required facts concisely without dollar breakdown. The only missing fact is the absence of Bureau of Reclamation or rural water authorization in the Energy-Water section, which slightly reduces completeness but does not introduce errors. Structure follows rules perfectly.

### summary_4 (score: 10)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer fully addresses all required facts, correctly distinguishes regular from continuing appropriations, and avoids all prohibited errors. The structure is concise and follows mode guidelines.

### summary_5 (score: 8)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs

**Judge Reasoning**: The answer provides a clear, multi-faceted summary of THUD programs for local governments, covering transportation (transit, airports) and housing/community development with specific examples. However, it fails to mention highway and safety programs, which are part of the division's transportation side, breaking one required fact. All prohibited errors are avoided, and the structure is appropriately concise with selective dollar figures. The omission is minor in the context of a summary, but prevents a perfect score.
