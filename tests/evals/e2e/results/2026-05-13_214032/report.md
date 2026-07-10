# E2E Eval Report

## Overall Summary

- **Questions**: 25 (25 scored)
- **Avg Score**: 7.7 / 10
- **Fact Recall**: 81.1%
- **Error Rate**: 0.9%
- **Classify Accuracy**: 96.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 5 | 6.8 | 68.6% | 3.8% | 100.0% | 100.0% |
| direct_account_amount | 5 | 9.0 | 85.7% | 0.0% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 5 | 7.6 | 76.0% | 0.0% | 80.0% | 100.0% |
| general_summary | 5 | 8.0 | 80.8% | 0.0% | 100.0% | 100.0% |
| reconciliation_breakdown | 5 | 7.0 | 88.3% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### direct_1 (score: 10)

**Question**: What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the major allowed uses?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately states the appropriation amount, lists major uses in categorical terms matching the gold reference, and correctly notes user fees credited without dollar breakdowns. No prohibited errors or structural violations. It adheres to the direct_account_amount mode perfectly.

### direct_2 (score: 10)

**Question**: What amount is provided for the USDA Food Safety and Inspection Service in FY2026, and what activities does it fund?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present and correctly stated. No prohibited errors were triggered. The answer adheres to structural rules by leading with the appropriation amount and naming major activities as categories without a detailed breakdown. The extra mentioned activities do not violate the guidelines.

### direct_3 (score: 10)

**Question**: What amount is appropriated for NASA Science in FY2026, and what is the funding available for?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer contains all required facts, avoids all prohibited errors, and follows the mode-specific structural rules perfectly by leading with the appropriation amount and providing only the necessary details without extraneous breakdowns.

### direct_4 (score: 9)

**Question**: What amount is appropriated for the EPA Environmental Programs and Management account in FY2026, and what does that acco
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Major set-asides include Geographic Programs $690,202,000

**Judge Reasoning**: Nearly all required facts are present with accurate amounts and support categories. The only missing fact is the Geographic Programs set-aside amount. No prohibited errors were triggered, and the answer follows structural rules perfectly. Minor omission prevents a perfect score.

### direct_5 (score: 6)

**Question**: What amount is appropriated for VA Medical Services in FY2026, and what kinds of care or services does it cover?
**Answer Mode**: expected=direct_account_amount actual=direct_account_amount MATCH
**Route**: MATCH

**Missed Facts**:
- Covered services include priority medical treatment and basic medical benefits for veterans in priority groups 1 through 6
- Covered services include prescription drugs, prosthetics, women veterans care, suicide prevention, caregiver support, PTSD services, rural health care, homelessness programs, telehealth, opioid prevention and treatment, and intimate partner violence assistance

**Judge Reasoning**: The answer correctly states the appropriation amount and includes FY2026 with reimbursements. It lists some service categories but omits key required details like coverage for priority groups 1-6 and a comprehensive list of covered services (e.g., prescription drugs, women veterans care). No prohibited errors or structural issues, but significant fact gaps reduce the score.

### broad_1 (score: 9)

**Question**: What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Triggered Errors**:
- Should not omit EPA/Interior for rural water or wastewater infrastructure: No mention of Interior or its agency role; only EPA and USDA are explicitly listed.

**Judge Reasoning**: All required facts are present, funding is properly grouped and labeled, and no sums are incorrectly added. The only minor shortfall is the omission of the Interior agency in connection with the authorization change, triggering a prohibited error, but overall the answer is comprehensive and well-structured.

### broad_2 (score: 4)

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
- Homelessness services include $107,000,000 for youth homelessness demonstration projects
- Youth homelessness system improvement grants may receive up to $25,000,000
- Supportive housing for persons with disabilities includes $287,000,000 for Section 811 project rental assistance and associated supportive services
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Structural Issues**:
- Rental assistance section presents only administrative expenses ($2.8B) and fails to identify the main tenant-based and project-based rental assistance accounts.
- Several major accounts (Public Housing Fund, most rental assistance) are omitted, leading to incomplete grouping by agency/account.
- Youth homelessness and supportive housing programs are missing entirely.

**Judge Reasoning**: The answer correctly identifies some Homeless Assistance Grants details but misses nearly all required facts on rental assistance, youth homelessness, and supportive housing. No prohibited errors, but significant information gaps result in a low score.

### broad_3 (score: 10)

**Question**: What FY2026 funding is available for airport infrastructure, runway improvements, or terminal upgrades?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Judge Reasoning**: The answer covers all required facts, correctly presents the $4B and $577M buckets with suballocations nested, avoids double-counting, and mentions runway improvements and terminal program support. Structure follows agency/account grouping with no fabricated totals.

### broad_4 (score: 5)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- COPS includes $84,000,000 for police-community relations
- COPS includes $50,000,000 for community violence intervention and prevention
- COPS includes $32,000,000 for Tribal law enforcement hiring and activities

**Structural Issues**:
- Police-community relations $84,000,000 should be nested under COPS but is listed as a separate top-level bullet.
- Tribal law enforcement $32,000,000 is not mentioned (also a fact gap).
- Amounts are not labeled by financial type (minor).

**Judge Reasoning**: The answer correctly identifies major accounts and amounts (OJP, COPS total, JAG, hiring), but it fails to nest the $84M police-community relations and the $50M community violence initiatives under COPS, missing the parent-child relationship. It also completely omits $32M for Tribal law enforcement, resulting in significant fact gaps. No prohibited errors triggered, but structural nesting issues lead to a mid-range score.

### broad_5 (score: 6)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Structural Issues**:
- Financial type labels are not consistently provided for all line items (e.g., Leaking Underground Storage Tank amount lacks explicit type such as 'trust fund program' detail). Minor but noted per mode rules.

**Judge Reasoning**: Answer correctly avoids prohibited totals and includes major Superfund and brownfields numbers. However, it misses the required $77.1M for CERCLA sections 311(a)/126(g) and the fee authority note, and does not break out the LUST cleanup sub-amount. These gaps reduce completeness to about a 6.

### mechanism_1 (score: 10)

**Question**: How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly identifies the absence of a full-year DHS amount, explains the continuing appropriations mechanism with rate-for-operations and apportionment details, notes the extension through February 13, 2026, and follows all structural rules including a compact bottom-line with mechanism bullets. No prohibited errors are triggered, and all required facts are present.

### mechanism_2 (score: 8)

**Question**: What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?
**Answer Mode**: expected=funding_mechanism_no_amount actual=general_summary MISMATCH
**Route**: MATCH

**Missed Facts**:
- It changes or extends the operative expiration date in the continuing appropriations framework

**Judge Reasoning**: The answer correctly identifies the act as a continuing appropriations measure using rate-for-operations, and it does not invent a total or mischaracterize it as a full-year bill. However, it fails to explicitly mention that the act changes or extends the operative expiration date, which is a key detail.

### mechanism_3 (score: 8)

**Question**: How does FY2026 handle FEMA Disaster Relief Fund funding under continuing appropriations?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The continuing appropriations period is extended to February 13, 2026

**Structural Issues**:
- Missing explicit extension date to February 13, 2026, as required by the 'extension' element of the funding mechanism explanation.

**Judge Reasoning**: The answer correctly captures the funding mechanism, rate-for-operations, FY2025 reference, and preservation of designations, with no prohibited errors. However, it omits the specific CR extension date of February 13, 2026, which is a required fact and a structural element, lowering the score slightly.

### mechanism_4 (score: 6)

**Question**: Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations mechanism?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The continuing resolution date is extended to February 13, 2026
- A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions

**Judge Reasoning**: The answer correctly identifies that no CISA dollar amount is given and describes the continuing-appropriations mechanism. However, it provides an incorrect end date (Jan 30 instead of Feb 13) and omits the required clarification that a dollar total would necessitate a separate line-item appropriation. No prohibited errors are triggered and structure is compact, but the factual gaps lower the score.

### mechanism_5 (score: 6)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The continuation applies to continuing projects and activities through the date specified in section 106(3)
- They may continue only at the most limited funding action permitted

**Judge Reasoning**: The answer covers most required facts but misses two specifics: the reference to section 106(3) for the continuation date and the explicit 'most limited funding action permitted' concept. It avoids all prohibited errors and follows structural rules.

### recon_1 (score: 9)

**Question**: Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what sho
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- FY2027 user fees accepted in FY2026 are excluded from FY2026 amounts under this heading

**Judge Reasoning**: The answer contains all required facts except the explicit statement that FY2027 user fees are excluded, though it discusses additional fee sources. No prohibited errors are triggered. The structure correctly separates Included and Not Added Separately sections, with transfers and limitations appropriately placed. The minor omission prevents a perfect score.

### recon_2 (score: 7)

**Question**: Break down NASA FY2026 funding by major account, and explain which amounts can be summed versus which are suballocations
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- $2,500,000 is a set-aside within the $46,500,000 OIG total
- $33,000,000 lease-proceeds availability cap is inside CECR and is not standalone budget authority

**Judge Reasoning**: The answer correctly lists all major NASA account amounts and cleanly separates suballocations, transfers, and caps. It violates no prohibited errors and follows structural rules perfectly. However, it omits two required facts: the $2,500,000 OIG set-aside and the $33,000,000 lease-proceeds cap. Overall, a thorough and accurate breakdown with minor omissions.

### recon_3 (score: 6)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- $7,000,000 is for section 306A(i)(2) grants
- $4,000,000 is for solid waste management grants

**Structural Issues**:
- The Included section contains both the total subsidy/grant amount ($445,864,564) and multiple component grant lines (e.g., Rural business development grants $21M, Grants to regional commissions $10M) that are suballocations of that total, causing double counting when all Included items are considered together.

**Judge Reasoning**: The answer captures most required facts and avoids prohibited errors, but omits two required facts ($7M for section 306A(i)(2) grants and $4M for solid waste management grants). It also violates the structural rule by including both parent totals and suballocations in the Included list, leading to potential double counting.

### recon_4 (score: 8)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000

**Judge Reasoning**: The answer correctly lists most required facts and avoids double-counting and structural issues, but it misses the $28,500,000 for Safe Drinking Water Act section 1459A(a)-(j) grants, which is a required fact.

### recon_5 (score: 5)

**Question**: Break down IRS FY2026 funding by taxpayer services, enforcement, operations support, and business systems modernization,
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Enforcement includes not more than $35,000,000 for Criminal Investigation investigative technology
- $275,000,000 remains available within Technology and Operations Support and is not added on top
- $10,000,000 is within Technology and Operations Support for equipment and facilities acquisition
- $1,000,000 is within Technology and Operations Support for research
- $20,000 is within Technology and Operations Support for official reception and representation expenses

**Judge Reasoning**: The answer correctly presents Taxpayer Services and Enforcement totals with their set-asides and avoids double counting or inventing amounts. However, it fails to provide a full reconciliation by not listing Technology and Operations Support as a category, and omits several required sub-item details, resulting in significant fact gaps. No prohibited errors were triggered.

### summary_1 (score: 7)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: The answer covers most required facts, including FDA funding, user fees, and the electronic prescribing restriction. It omits the obligation plan fact, but avoids prohibited errors and follows the general_summary structure with concise bullets and selective dollar figures.

### summary_2 (score: 5)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water activities include Bureau of Reclamation and water storage or restoration projects
- The division also funds administration and oversight, including Departmental Administration and the Office of Inspector General

**Judge Reasoning**: The answer covers DOE and USACE activities but misses several key required facts: Bureau of Reclamation, tribal energy, power administration facilities, and Departmental Administration/IG. No prohibited errors or structural issues. Major fact gaps result in a score of 5.

### summary_3 (score: 8)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA

**Judge Reasoning**: The answer effectively covers USDA, EPA, and Energy-Water with clear mechanisms and avoids prohibited errors, but it omits the Alaska rural and Native Village infrastructure component in EPA, which is a required fact. Otherwise, well-structured and concise.

### summary_4 (score: 10)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately captures all required facts, makes no prohibited errors, and follows the general_summary structural rules with concise bullet points and no unnecessary details.

### summary_5 (score: 10)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer covers all required facts about THUD's local government programs, avoids prohibited errors, and adheres to the general_summary structure with concise bullets and selective dollar figures.
