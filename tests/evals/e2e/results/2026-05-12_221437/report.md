# E2E Eval Report

## Overall Summary

- **Questions**: 1 (1 scored)
- **Avg Score**: 7.0 / 10
- **Fact Recall**: 72.7%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 1 | 7.0 | 72.7% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_4 (score: 7)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- COPS includes $84,000,000 for police-community relations
- COPS includes $50,000,000 for community violence intervention and prevention
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Structural Issues**:
- Police-community relations ($84M) and community violence intervention ($50M) should be nested under COPS instead of listed as separate top-level buckets.

**Judge Reasoning**: The answer correctly reports most large funding lines and avoids prohibited errors, but fails to nest two COPS subprograms under the parent account and omits two minor targeted grant amounts ($5M cybercrimes, $7.5M Daniel Anderl), resulting in moderate fact and structural gaps.
