# E2E Eval Report

## Overall Summary

- **Questions**: 4 (4 scored)
- **Avg Score**: 4.8 / 10
- **Fact Recall**: 59.0%
- **Error Rate**: 10.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 3 | 5.3 | 61.8% | 6.2% | 100.0% | 100.0% |
| general_summary | 1 | 3.0 | 40.0% | 25.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_2 (score: 2)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Tenant-based rental assistance is appropriated $34,438,557,000
- Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025
- Tenant-based rental assistance includes $4,000,000,000 available October 1, 2026
- Tenant-based rental assistance includes $34,957,000,000 for renewals of expiring Section 8 tenant-based annual contributions contracts
- Project-based rental assistance is provided $18,143,000,000
- Homeless Assistance Grants receive $4,417,000,000
- Homeless Assistance Grants include $290,000,000 for Emergency Solutions Grants
- Homeless Assistance Grants include $4,010,000,000 for Continuum of Care and rural housing stability assistance
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis

**Triggered Errors**:
- Should not omit the main Homeless Assistance Grants parent account when answering homelessness services: The answer mentions youth homelessness demo projects and non-competitive renewals but does not mention the $4,417,000,000 Homeless Assistance Grants account.

**Structural Issues**:
- Missing major HUD accounts such as Tenant-based Rental Assistance, Project-based Rental Assistance, and Homeless Assistance Grants. The 'Rental assistance' bucket only includes Section 811, which is a subset, and the 'Homelessness services' bucket omits the main account. Suballocations are nested but top-level parent accounts are absent.

**Judge Reasoning**: The answer omits the most significant rental assistance and homelessness funding streams, providing only fragmentary information. While it correctly avoids a single total, the extensive omissions render it substantially incomplete for the user's question.

### broad_4 (score: 7)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Other targeted grants include $5,000,000 for cybercrimes against individuals
- Other targeted grants include $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- COPS suballocations (e.g., $84m police-community relations, $18m community policing, $15m de-escalation) are listed as top-level line items rather than nested under the $800m COPS parent
- State and local law enforcement/violence-prevention line items are not clearly grouped under either OJP or COPS, causing ambiguity about parent-child relationships

**Judge Reasoning**: Most required facts are present, but two targeted grant amounts ($5m cybercrimes, $7.5m Daniel Anderl) are missing. The structural grouping violates the nesting rule, with COPS sub-programs listed outside the parent account. No prohibited errors were triggered.

### broad_5 (score: 7)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Judge Reasoning**: The answer avoids prohibited errors and satisfies structural rules, and includes most required facts, but omits the $77,100,000 for Superfund activities under CERCLA sections 311(a) and 126(g) and does not mention the brownfields fee authority under section 3024. These omissions prevent a perfect score.

### summary_5 (score: 3)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-HUD covers transportation and housing/urban development programs relevant to local governments
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs

**Triggered Errors**:
- Should not omit either transportation or housing/HUD coverage: answer omits transportation entirely; only housing and community development discussed

**Judge Reasoning**: The answer covers only the housing and community development side of THUD, completely omitting transportation programs, which violates a key requirement. While it provides some relevant housing details and follows structural rules, the omission of transportation is a major gap, resulting in a low score.
