# E2E Eval Report

## Overall Summary

- **Questions**: 4 (4 scored)
- **Avg Score**: 5.5 / 10
- **Fact Recall**: 65.8%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 3 | 5.3 | 63.6% | 0.0% | 100.0% | 100.0% |
| general_summary | 1 | 6.0 | 80.0% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

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
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Judge Reasoning**: The answer correctly includes Homeless Assistance Grants and some supportive housing programs, but omits the primary tenant-based and project-based rental assistance appropriations (over $52 billion combined), which are central to the city's query. It also misses the $10M national homeless data analysis required fact and fails to clarify the Public Housing Fund distinction. Structural grouping is okay, but massive fact gaps reduce the score to 4.

### broad_4 (score: 6)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- COPS includes $32,000,000 for Tribal law enforcement hiring and activities
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- '$84,000,000 for initiatives to improve police-community relations' is a COPS suballocation but is not nested under the COPS parent bucket.
- '$50,000,000 for community violence intervention and prevention' is a COPS suballocation but is listed under a separate grant section rather than nested.
- Missing required fact: $32,000,000 for Tribal law enforcement hiring and activities under COPS.
- Missing required fact: $5,000,000 for cybercrimes against individuals.

**Judge Reasoning**: The answer correctly captures most major funding amounts and avoids additive errors, but it omits two required specific allocations ($32M Tribal, $5M cybercrimes) and misplaces the $84M and $50M COPS suballocations outside the parent bucket, violating nesting structure. These gaps and structural issue reduce the score.

### broad_5 (score: 6)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Judge Reasoning**: Answer avoids a summed total and lists major accounts correctly, but omits the $77.1M for CERCLA sections 311(a)/126(g), the $64.583M cleanup portion of LUST, and the fee authority note, leading to significant fact gaps. Structure complies well.

### summary_5 (score: 6)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs

**Structural Issues**:
- Dollar figures are used extensively for multiple specific programs ($50,000,000, $25,000,000, $137,426,000, etc.) when a summary could convey scope without exact amounts, violating 'Dollar figures only when they directly explain the answer'

**Judge Reasoning**: The answer covers both transportation and housing sides but omits key HUD rental assistance programs required by the gold standard. While it avoids major errors and structural tables, it overuses specific dollar figures, reducing conciseness and violating the structural rule.
