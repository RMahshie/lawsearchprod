# E2E Eval Report

## Overall Summary

- **Questions**: 2 (2 scored)
- **Avg Score**: 5.0 / 10
- **Fact Recall**: 60.0%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 2 | 5.0 | 60.0% | 0.0% | 100.0% | 100.0% |

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
- Homelessness services include $107,000,000 for youth homelessness demonstration projects
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Structural Issues**:
- No financial type labels (e.g., 'appropriation') on amounts
- Rental assistance funding is listed as isolated sub-items without the parent Tenant-Based Rental Assistance account or total
- Youth homelessness funding ($25M) is not nested under the broader Homelessness Services or HUD parent, and the $107M parent is omitted
- The large Public Housing Fund is omitted entirely, missing a key affordable housing support

**Judge Reasoning**: The answer correctly identifies several homelessness and supportive housing amounts, but entirely omits the massive tenant-based and project-based rental assistance appropriations (over $50 billion combined), making it critically incomplete for the question. The structural presentation also lacks financial type labels and proper nesting.

### broad_4 (score: 6)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- OJP is $2,400,000,000
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- COPS subprograms ($18M community policing development and $15M de-escalation training) are listed under 'Other direct lines' instead of nested under the COPS parent account
- No explicit OJP agency grouping; the $2.4B amount is labeled under a program name instead of the parent OJP account
- Various amounts in 'Other direct lines' are not clearly grouped by agency/account, mixing COPS, OJP, and other entities

**Judge Reasoning**: The answer correctly presents major COPS and Byrne JAG figures with proper nesting, but it fails to label the $2.4B as OJP and omits two required targeted grants. Structurally, COPS suballocations are split across sections and a catch-all list violates agency grouping.
