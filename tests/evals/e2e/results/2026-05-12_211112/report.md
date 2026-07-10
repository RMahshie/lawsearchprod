# E2E Eval Report

## Overall Summary

- **Questions**: 9 (9 scored)
- **Avg Score**: 6.8 / 10
- **Fact Recall**: 76.5%
- **Error Rate**: 2.3%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 3 | 4.3 | 51.5% | 6.2% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 2 | 7.5 | 63.6% | 0.0% | 100.0% | 100.0% |
| general_summary | 2 | 6.5 | 60.0% | 0.0% | 100.0% | 100.0% |
| reconciliation_breakdown | 2 | 10.0 | 100.0% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

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

**Judge Reasoning**: The answer adequately covers Homeless Assistance Grants and youth homelessness, but entirely omits the massive tenant-based and project-based rental assistance appropriations ($34.4B and $18.1B respectively) as well as Section 811 supportive housing. These are critical omissions, making the answer highly incomplete for a city seeking rental assistance.

### broad_4 (score: 5)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- COPS includes $84,000,000 for police-community relations
- COPS includes $50,000,000 for community violence intervention and prevention
- COPS includes $18,000,000 for community policing development
- COPS includes $15,000,000 for de-escalation training
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- COPS suballocations ($84M police-community relations, $50M community violence intervention, $18M community policing development, $15M de-escalation training) are not nested under COPS; listed in a flat 'Other' list instead.
- The nested breakdown of $84M incorrectly includes $50M community violence intervention as a sub-item, conflicting with the separate required fact of $50M community violence intervention.

**Judge Reasoning**: The answer correctly identifies major funding totals for COPS ($800M) and OJP ($2.4B with $964M JAG) and some COPS suballocations, but fails to properly nest COPS suballocations under the COPS account and omits required facts for cybercrimes and Daniel Anderl grants, leading to structural and factual gaps.

### broad_5 (score: 5)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 104(k) brownfields grants are $98,000,000
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Triggered Errors**:
- Should not omit Hazardous Substance Superfund or brownfields grants: Hazardous Substance Superfund is included, but brownfields grants ($98M under section 104(k)) are entirely omitted.

**Judge Reasoning**: The answer correctly identifies that no single total exists and lists several relevant accounts, including Hazardous Substance Superfund and CERCLA section 128 grants. However, it omits brownfields grants ($98M), other Superfund-related activities ($77.1M), the LUST cleanup-specific amount ($64.583M), and fee authority. These omissions reduce completeness, though the structure avoids aggregating mixed funding types.

### mechanism_4 (score: 7)

**Question**: Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations mechanism?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The continuing resolution date is extended to February 13, 2026
- A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions

**Judge Reasoning**: The answer correctly identifies that no specific CISA dollar amount is provided and explains the continuing-appropriations mechanism. However, it misstates the CR end date as January 30, 2026 instead of February 13, 2026, and does not explicitly state that a dollar total would require a separate line-item appropriation. No prohibited errors were triggered, and the structure follows the mode rules.

### mechanism_5 (score: 8)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- The continuation applies to continuing projects and activities through the date specified in section 106(3)
- Payments and reimbursements are made only to the extent and in the amounts provided in advance in appropriations Acts

**Judge Reasoning**: The answer covers most required facts, accurately describes the CR mechanism, avoids prohibited errors, and follows structural rules, but misses explicit mention of section 106(3) and the precise statement about payments/reimbursements being limited to advance appropriations.

### recon_1 (score: 10)

**Question**: Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what sho
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: All required facts are present and accurately quoted. No prohibited errors are triggered. The answer follows all structural rules with clear Included and Not Added Separately sections, proper handling of suballocations and caps, and no double counting.

### recon_3 (score: 10)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Judge Reasoning**: The answer includes all required facts with clear evidence, avoids all prohibited errors, and perfectly follows the reconciliation_breakdown structure by separating Included and Not Added Separately items and labeling financial types correctly.

### summary_3 (score: 9)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material

**Judge Reasoning**: The answer covers all three agencies and their distinct mechanisms without providing dollar figures or a total, satisfying most required facts and avoiding prohibited errors. It fails to explicitly mention 'rural water authorization/project material' in the Energy-Water section, giving only an implicit reference via 'selected western water projects', which makes one required fact less clearly present. Structure is concise and follows mode rules.

### summary_5 (score: 4)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs
- The division contains distinct accounts and programs rather than one single local-government funding pool

**Judge Reasoning**: The answer covers transportation programs reasonably but omits major HUD programs like rental assistance and public housing. It fails to state that the division contains distinct accounts/programs. No errors triggered, but several required facts are missing, resulting in significant gaps.
