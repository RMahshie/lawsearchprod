# E2E Eval Report

## Overall Summary

- **Questions**: 1 (1 scored)
- **Avg Score**: 7.0 / 10
- **Fact Recall**: 78.6%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 1 | 7.0 | 78.6% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_2 (score: 7)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis
- Homelessness services include $107,000,000 for youth homelessness demonstration projects
- Youth homelessness system improvement grants may receive up to $25,000,000

**Judge Reasoning**: The answer clearly organizes separate HUD funding lanes and avoids a misleading total. It includes most key rental assistance and homeless grant numbers, but omits three required homelessness facts: $10M for data analysis, $107M youth demo projects, and $25M youth improvement grants. No prohibited errors and well-structured grouping.
