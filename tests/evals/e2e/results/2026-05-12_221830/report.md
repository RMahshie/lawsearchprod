# E2E Eval Report

## Overall Summary

- **Questions**: 4 (4 scored)
- **Avg Score**: 6.5 / 10
- **Fact Recall**: 76.3%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 3 | 7.0 | 78.8% | 0.0% | 100.0% | 100.0% |
| general_summary | 1 | 5.0 | 60.0% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_2 (score: 7)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis
- Homelessness services include $107,000,000 for youth homelessness demonstration projects

**Judge Reasoning**: The answer correctly groups funding by HUD program lanes, avoids prohibited errors, and follows structural rules. However, it misses three required facts: the specific availability date for previously appropriated tenant-based rental assistance, the $10,000,000 for national homeless data analysis, and the $107,000,000 for youth homelessness demonstration projects. These omissions prevent a higher score.

### broad_4 (score: 7)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- Suballocations for COPS (community violence, community policing, de-escalation) are not nested under the COPS account; they appear in a separate flat list.
- Grouping by agency/account is incomplete: OJP and COPS subprograms are not clearly parented under their respective accounts.

**Judge Reasoning**: Most required facts are present except the two specific grant amounts for cybercrimes and Daniel Anderl. No prohibited errors were triggered. Structural issues exist with nesting of COPS suballocations, but the answer avoids summation pitfalls. Overall informative but missing minor details.

### broad_5 (score: 7)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 128 grants are $46,250,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Judge Reasoning**: The answer correctly separates accounts and avoids a single total. It covers most key figures but omits CERCLA section 128 grants and the LUST cleanup subamount, and does not mention the fee authority. No prohibited errors and structural rules followed. Overall solid but missing some specific funding lines.

### summary_5 (score: 5)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs

**Judge Reasoning**: The answer gives a basic overview of housing and transportation support but omits major required details: transportation specifics like airport/highway/transit grants and safety, and HUD programs like rental assistance, homelessness services, and supportive housing. No structural or error violations, but significant factual gaps reduce the score.
