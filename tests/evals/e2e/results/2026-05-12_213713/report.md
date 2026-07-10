# E2E Eval Report

## Overall Summary

- **Questions**: 4 (4 scored)
- **Avg Score**: 4.2 / 10
- **Fact Recall**: 57.9%
- **Error Rate**: 5.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 3 | 4.3 | 57.6% | 6.2% | 100.0% | 100.0% |
| general_summary | 1 | 4.0 | 60.0% | 0.0% | 100.0% | 100.0% |

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

**Structural Issues**:
- $10,000,000 for national homeless data analysis is incorrectly placed under Youth homelessness instead of Homeless Assistance Grants
- Missing major rental assistance accounts (Tenant-based and Project-based) violates comprehensive grouping by account

**Judge Reasoning**: The answer correctly includes homelessness and some affordable housing programs but completely omits the large tenant-based ($34.4B) and project-based ($18.1B) rental assistance accounts, which are central to the question. It also misplaces the $10M homeless data analysis under youth homelessness. No prohibited errors were triggered, and structure is partially followed, but the missing core facts severely limit the answer's usefulness for a city seeking rental assistance information.

### broad_4 (score: 6)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- COPS includes $84,000,000 for police-community relations
- COPS includes $50,000,000 for community violence intervention and prevention
- COPS includes $32,000,000 for Tribal law enforcement hiring and activities
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- The $84,000,000 police‑community relations and $50,000,000 community violence intervention amounts should be nested under the COPS parent account, but they appear as a separate top‑level bullet instead.

**Judge Reasoning**: The answer correctly frames the funding under CJS and provides the major OJP and COPS totals along with several key subprograms. However, it omits Tribal law enforcement, cybercrimes, and Daniel Anderl grants, fails to explicitly attribute the police‑community relations and community violence prevention amounts to COPS, and exhibits a structural nesting error. No prohibited errors are triggered, but the missing facts and structural flaw hold the score to a 6.

### broad_5 (score: 4)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 128 grants are $46,250,000
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- Environmental Programs and Management is $3,114,671,000 and includes administrative costs of the brownfields program, but it is broader than cleanup funding
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Triggered Errors**:
- Should not imply the full Environmental Programs and Management account is cleanup funding: Grouped under 'Brownfields cleanup' heading: 'Key buckets: - Brownfields cleanup: Environmental Programs and Management receives...'

**Structural Issues**:
- Funds grouped by cleanup purpose rather than agency/account
- Financial types not labeled for all amounts
- Suballocations not nested under parent accounts

**Judge Reasoning**: The answer correctly avoids a single total and provides Hazardous Substance Superfund and brownfields 104(k) grants, but it omits CERCLA 128 grants, superfund-related activities ($77.1M), and the cleanup portion of Leaking Underground Storage Tank fund. Moreover, grouping EPM under 'Brownfields cleanup' implies it is cleanup funding, triggering a prohibited error. Structural grouping by purpose rather than account also violates mode rules.

### summary_5 (score: 4)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs

**Judge Reasoning**: The answer covers some local-government programs but omits core HUD categories like rental assistance and public housing, and misses key transportation areas like airport and highway grants. This results in a significant fact gap, though no errors are triggered and structure is fine.
