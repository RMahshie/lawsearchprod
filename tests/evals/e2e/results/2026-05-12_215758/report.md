# E2E Eval Report

## Overall Summary

- **Questions**: 1 (1 scored)
- **Avg Score**: 3.0 / 10
- **Fact Recall**: 35.7%
- **Error Rate**: 16.7%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 1 | 3.0 | 35.7% | 16.7% | 100.0% | 100.0% |

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
- Homeless Assistance Grants receive $4,417,000,000
- Homeless Assistance Grants include $290,000,000 for Emergency Solutions Grants
- Homeless Assistance Grants include $4,010,000,000 for Continuum of Care and rural housing stability assistance
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis

**Triggered Errors**:
- Should not omit the main Homeless Assistance Grants parent account when answering homelessness services: no mention of the $4,417,000,000 Homeless Assistance Grants account; only sub-programs listed

**Structural Issues**:
- Funding not grouped by standard agency/account; ad-hoc buckets mix Public Housing Fund with Section 8 admin, and homelessness sub-accounts are not nested under their parent Homeless Assistance Grants account
- Sub-allocations (e.g., $52M CoC set-aside) are presented as top-level homelessness services rather than nested under the parent grant account

**Judge Reasoning**: The answer includes some smaller programs but omits the major tenant-based and project-based rental assistance totals and the main Homeless Assistance Grants account, failing to provide a complete picture of available funding. It triggers a prohibited error by omitting the Homeless Assistance Grants parent account and violates structural rules by not grouping by proper accounts or nesting sub-allocations.
