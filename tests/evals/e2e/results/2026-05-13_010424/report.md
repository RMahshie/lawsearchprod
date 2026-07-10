# E2E Eval Report

## Overall Summary

- **Questions**: 2 (2 scored)
- **Avg Score**: 7.5 / 10
- **Fact Recall**: 76.9%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 2 | 7.5 | 76.9% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_2 (score: 8)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025
- Supportive housing for persons with disabilities includes $287,000,000 for Section 811 project rental assistance and associated supportive services
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Structural Issues**:
- National homeless data analysis project ($10,000,000) is placed under a separate 'Homelessness innovation/youth projects' bucket instead of under the Homeless Assistance Grants parent account.

**Judge Reasoning**: The answer accurately presents the key FY2026 funding streams for rental assistance and homelessness services, avoiding additive totals and explaining timing. It misses the Section 811 supportive housing funding and does not specify the October 1, 2025 availability for previously appropriated tenant-based funds, and it misplaces the $10M data analysis under a non-parent heading, slightly reducing precision and completeness.

### broad_4 (score: 7)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- COPS includes $32,000,000 for Tribal law enforcement hiring and activities
- Other targeted grants include $5,000,000 for cybercrimes against individuals
- Other targeted grants include $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- Police-community relations $84,000,000 and community violence intervention $50,000,000 should be nested under COPS parent account, but they are presented as a separate top-level bullet.
- Grants to improve the criminal justice response $60,500,000 is not clearly nested under OJP or another parent account.

**Judge Reasoning**: The answer includes most required facts but omits several specific grants (Tribal law enforcement, cybercrimes, Daniel Anderl) and has structural issues with nesting suballocations under parent accounts. No prohibited errors were triggered.
