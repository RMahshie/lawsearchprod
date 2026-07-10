# E2E Eval Report

## Overall Summary

- **Questions**: 25 (25 scored)
- **Avg Score**: 8.0 / 10
- **Fact Recall**: 86.6%
- **Error Rate**: 1.7%
- **Classify Accuracy**: 96.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 5 | 8.0 | 86.3% | 3.8% | 100.0% | 100.0% |
| direct_account_amount | 5 | 7.8 | 81.0% | 0.0% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 5 | 8.8 | 84.0% | 0.0% | 100.0% | 100.0% |
| general_summary | 5 | 6.6 | 61.5% | 4.8% | 80.0% | 100.0% |
| reconciliation_breakdown | 5 | 8.6 | 95.7% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### direct_1 (score: 8)

**Question**: What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- User fees are credited to the account, including prescription drug, medical device, human generic drug, biosimilar, animal drug, generic new animal drug, and tobacco product user fees

**Judge Reasoning**: The answer correctly states the appropriation amount and lists all major uses, but it fails to enumerate the specific user fees credited to the account (a required fact). No prohibited errors and structural rules are followed, resulting in a score of 8.

### direct_2 (score: 9)

**Question**: What amount is provided for the USDA Food Safety and Inspection Service in FY2026, and what activities does it fund?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Major activities include inspection and enforcement for meat, poultry, and egg products

**Judge Reasoning**: The answer correctly states the main appropriation, referred acts, $1M fee credit, and humane slaughter inspections; however it does not explicitly name inspection/enforcement of meat, poultry, and egg products as a funded activity, despite the opening phrase implying it. No errors or structural violations.

### direct_3 (score: 10)

**Question**: What amount is appropriated for NASA Science in FY2026, and what is the funding available for?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present and accurately stated. No prohibited errors were triggered. The answer leads with the appropriation amount, names major allowed uses as categories, and follows all structural rules for the direct_account_amount mode.

### direct_4 (score: 7)

**Question**: What amount is appropriated for the EPA Environmental Programs and Management account in FY2026, and what does that acco
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Major set-asides include Geographic Programs $690,202,000

**Structural Issues**:
- Includes specific dollar amounts for set-asides (Energy Star, grants, National Priorities) instead of naming categories without dollar figures as required by mode-specific rules.

**Judge Reasoning**: The answer correctly identifies the total appropriation and most supported activities, but omits the required Geographic Programs set-aside, which is a significant gap. It also includes dollar amounts for some set-asides contrary to the structural rule. No prohibited errors were triggered.

### direct_5 (score: 5)

**Question**: What amount is appropriated for VA Medical Services in FY2026, and what kinds of care or services does it cover?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Covered services include prescription drugs, prosthetics, women veterans care, suicide prevention, caregiver support, PTSD services, rural health care, homelessness programs, telehealth, opioid prevention and treatment, and intimate partner violence assistance

**Judge Reasoning**: The answer correctly provides the main appropriation amount and adheres to structural rules, but it omits many required covered services (e.g., suicide prevention, caregiver support, PTSD services), resulting in a significant fact gap.

### broad_1 (score: 10)

**Question**: What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present with clear evidence, no prohibited errors are triggered, and the answer adheres perfectly to the broad_topic_total structural rules by grouping by agency/account, avoiding fabricated totals, labeling financial types, and nesting suballocations under parent accounts.

### broad_2 (score: 5)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Homeless Assistance Grants receive $4,417,000,000
- Homeless Assistance Grants include $290,000,000 for Emergency Solutions Grants
- Homeless Assistance Grants include $4,010,000,000 for Continuum of Care and rural housing stability assistance

**Triggered Errors**:
- Should not omit the main Homeless Assistance Grants parent account when answering homelessness services: Homelessness services section mentions only Sec. 244 non-competitive renewal and lists suballocations ($10M, $107M, up to $25M) without the overall $4,417,000,000 parent account

**Structural Issues**:
- Homelessness services suballocations ($10M, $107M, up to $25M) are not nested under the parent Homeless Assistance Grants account, which is omitted entirely; the parent total of $4,417,000,000 is missing

**Judge Reasoning**: The answer covers rental assistance well but omits the main Homeless Assistance Grants total and several required subcomponents ($290M ESG, $4.01B CoC), violating a prohibited error. Though structural grouping is attempted, the homelessness section fails to nest suballocations under the missing parent, causing a structural issue. These gaps significantly affect completeness.

### broad_3 (score: 10)

**Question**: What FY2026 funding is available for airport infrastructure, runway improvements, or terminal upgrades?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present and clearly evidenced, no prohibited errors are triggered, the answer properly groups funding by account with nested suballocations, avoids fabricated totals, and includes the requested runway/terminal examples.

### broad_4 (score: 6)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Local law enforcement, community violence prevention, and police hiring funding is primarily in OJP and COPS
- OJP is $2,400,000,000
- OJP includes $964,000,000 for the Edward Byrne Memorial JAG program

**Structural Issues**:
- Byrne JAG is not nested under OJP, and OJP is never mentioned as the parent account
- Several COPS subprograms ($84M for police-community relations, $18M for community policing development, $15M for de-escalation training) are listed in a separate 'Other direct local-law-enforcement' bucket rather than nested under the COPS account

**Judge Reasoning**: The answer correctly provides many COPS amounts and targeted grants but entirely omits OJP as the parent account for Byrne JAG and its total, and misplaces several COPS subprograms outside the COPS bucket, violating structural requirements.

### broad_5 (score: 9)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Environmental Programs and Management is $3,114,671,000 and includes administrative costs of the brownfields program, but it is broader than cleanup funding

**Judge Reasoning**: The answer includes all critical funding lines, clearly warns against a clean total, and avoids all prohibited errors. The only minor omission is the explicit statement that Environmental Programs and Management is broader than cleanup funding, though the context implies it. Structure and grouping follow mode-specific rules.

### mechanism_1 (score: 10)

**Question**: How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present and accurately described. No prohibited errors are triggered. The answer follows the mode-specific structural rules: it does not hallucinate a dollar amount, explains the funding mechanism clearly, and provides a compact response without unnecessary sections.

### mechanism_2 (score: 10)

**Question**: What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately describes the Further Continuing Appropriations Act as a continuing resolution that extends funding via the rate-for-operations mechanism under prior year laws, avoids any dollar amount, and follows the compact structure with mechanism bullets. All required facts are covered with no errors.

### mechanism_3 (score: 8)

**Question**: How does FY2026 handle FEMA Disaster Relief Fund funding under continuing appropriations?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Prior disaster-relief designations are preserved for amounts incorporated by reference

**Judge Reasoning**: The answer accurately states no explicit DRF dollar total, explains the CR mechanism with rate-for-operations, apportionment, extension to Feb 13, 2026, and reference to FY2025 appropriations. It avoids all prohibited errors and follows structural rules. However, it misses the required fact that prior disaster-relief designations are preserved, which prevents a perfect score.

### mechanism_4 (score: 7)

**Question**: Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations mechanism?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The continuing resolution date is extended to February 13, 2026
- A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions

**Judge Reasoning**: The answer correctly identifies only a mechanism and no dollar amount, and explains the CR well. However, it mistakenly gives the end date as January 30, 2026 (should be February 13) and omits the required fact that a CISA dollar total would need a separate line-item appropriation.

### mechanism_5 (score: 9)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Payments and reimbursements are made only to the extent and in the amounts provided in advance in appropriations Acts

**Judge Reasoning**: The answer covers almost all required facts, avoids prohibited errors, and follows the compact structural rules. The only missing element is the condition that payments are made only to the extent and in amounts provided in advance, but this is a minor omission in an otherwise accurate and well-structured response.

### recon_1 (score: 5)

**Question**: Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what sho
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Programmatic breakdown includes Other activities $343,354,000
- Programmatic allocations reconcile to $6,957,972,000
- FY2027 user fees accepted in FY2026 are excluded from FY2026 amounts under this heading

**Structural Issues**:
- Programmatic breakdown does not include Other activities amount ($343,354,000), so listed lines do not sum to the total. The reconciliation claim is invalid.
- Missing a required programmatic line impairs parent-child math.

**Judge Reasoning**: The answer correctly identifies most programmatic and financing details and handles suballocations well, but it omits the 'Other activities' appropriation line ($343,354,000), causing the reconciliation to be incorrect and incomplete. This significant gap, along with the missed FY2027 user-fee exclusion fact, results in a score of 5.

### recon_2 (score: 8)

**Question**: Break down NASA FY2026 funding by major account, and explain which amounts can be summed versus which are suballocations
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- CECR prior-year project use is limited to not more than 20 percent or $50,000,000, whichever is less

**Judge Reasoning**: All required facts are present except the specific numerical limit for CECR prior-year project use, which is omitted. No prohibited errors, and structural rules are followed perfectly. The omission of the exact cap (20% or $50M) is a minor factual gap, preventing a perfect score.

### recon_3 (score: 10)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present and correctly categorized. No prohibited errors are triggered. The answer adheres to the reconciliation_breakdown structure with clear Included and Not Added Separately sections, preserving parent-child relationships and financial-type labels.

### recon_4 (score: 10)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts, avoids every prohibited error, and strictly follows the reconciliation breakdown structure with clear Included and Not Added Separately sections. Suballocations are correctly placed outside the main total, and the non-water items are noted. The answer is accurate and complete.

### recon_5 (score: 10)

**Question**: Break down IRS FY2026 funding by taxpayer services, enforcement, operations support, and business systems modernization,
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly identifies the FSGG section, provides the three IRS funding amounts, notes the absence of a BSM figure, and breaks down suballocations without double counting. All required facts are present, no prohibited errors are triggered, and the structural rules are followed.

### summary_1 (score: 4)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment
- The division bars use of funds to implement electronic distribution of prescribing information for certain drugs unless federal law authorizes it

**Triggered Errors**:
- Should not omit the electronic prescribing-information restriction: answer omits any mention of the electronic prescribing-information restriction

**Judge Reasoning**: The answer captures only the basic funding mechanism but omits critical required facts about specific user fees, the obligation plan, and the electronic prescribing restriction, triggering a prohibited error. While structure is acceptable, significant factual gaps reduce the score.

### summary_2 (score: 4)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water and civil works activities include hydroelectric facility operations and upgrades
- Supported water activities include Bureau of Reclamation and water storage or restoration projects
- Supported water activities include regulatory program activities for navigable waters and wetlands
- The division also funds administration and oversight, including Departmental Administration and the Office of Inspector General

**Judge Reasoning**: The answer covers broad categories but misses several required specifics: fossil energy R&D, power administration facilities, hydroelectric operations, Bureau of Reclamation, regulatory activities, and departmental administration/OIG. No prohibited errors or structural issues. Score reflects significant fact gaps.

### summary_3 (score: 9)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer covers all required facts—mentioning USDA, EPA, and Energy-Water, describing their distinct mechanisms, and avoiding a single total. It complies with prohibitions by not providing a detailed breakdown or omitting an agency. Structure is concise with appropriate use of bullets and limited dollar figures. Minor shortfall: Energy-Water's Reclamation mention could explicitly reference rural water authorization, but it is still implied.

### summary_4 (score: 10)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=funding_mechanism_no_amount MISMATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts, avoids all prohibited errors, and follows the mode-specific structure by providing a bottom-line summary and mechanism-focused bullets without invented dollar amounts.

### summary_5 (score: 6)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs
- The answer should be concise and explanatory rather than a detailed funding ledger

**Structural Issues**:
- Includes numerous dollar figures that do not directly explain the summary, violating 'Dollar figures only when they directly explain the answer'

**Judge Reasoning**: The answer covers transportation and some HUD programs but omits key HUD items like tenant-based and project-based rental assistance. It lists many dollar amounts, making it less concise and more like a ledger, failing to adhere to mode-specific guidance. Overall, it is a decent but incomplete summary.
