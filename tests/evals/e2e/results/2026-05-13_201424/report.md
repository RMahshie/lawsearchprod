# E2E Eval Report

## Overall Summary

- **Questions**: 4 (4 scored)
- **Avg Score**: 6.2 / 10
- **Fact Recall**: 70.0%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 3 | 5.7 | 63.6% | 0.0% | 100.0% | 100.0% |
| reconciliation_breakdown | 1 | 8.0 | 82.4% | 0.0% | 100.0% | 100.0% |

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
- Supportive housing for persons with disabilities includes $287,000,000 for Section 811 project rental assistance and associated supportive services
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Structural Issues**:
- Rental assistance section does not include the required parent account or suballocations for tenant-based and project-based rental assistance appropriations.

**Judge Reasoning**: The answer correctly covers homelessness service appropriations in detail but completely omits the massive tenant-based and project-based rental assistance appropriations, as well as supportive housing for persons with disabilities and the Public Housing Fund. While it avoids prohibited errors and partially meets structural rules, the missing core facts severely limit its usefulness.

### broad_4 (score: 6)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- COPS includes $84,000,000 for police-community relations
- COPS includes $50,000,000 for community violence intervention and prevention
- COPS includes $32,000,000 for Tribal law enforcement hiring and activities

**Structural Issues**:
- Funding not properly grouped by agency/account: COPS suballocations (police-community relations, community violence intervention) are presented as top-level buckets rather than nested under COPS
- Suballocations should be nested under their parent account: $84M police-community relations and $50M community violence intervention are not shown as part of the $800M COPS total
- Amounts mostly lack financial type labels (e.g., 'grant', 'appropriation') beyond a few cases

**Judge Reasoning**: The answer includes most required figures but fails to state that $84M for police-community relations and $50M for community violence intervention are part of COPS, and omits COPS Tribal funding entirely. Structural rules are violated by not nesting these suballocations under COPS. No prohibited errors were triggered.

### broad_5 (score: 7)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Structural Issues**:
- Suballocations like CERCLA section 104(k) and 128 grants are not nested under a parent account (e.g., EPA's Hazardous Substance Superfund or State and Tribal Assistance Grants); instead they appear under a non-standard 'CERCLA remediation/grant lanes' header.
- The Leaking Underground Storage Tank Trust Fund amount is listed as a top-level item without clear account grouping within the department.

**Judge Reasoning**: The answer correctly identifies key funding lines and emphasizes the lack of a clean total. However, it mischaracterizes the full Leaking Underground Storage Tank Trust Fund Program amount as cleanup money (omitting the $64,583,000 subset) and fails to mention the fee authority note. Structurally, grant suballocations are not properly nested, but no prohibited errors were triggered.

### recon_4 (score: 8)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000
- STAG includes Save Our Seas section 302(a) grants of $3,500,000
- The STAG account includes non-water items outside this breakdown

**Judge Reasoning**: The answer provides a well-structured reconciliation breakdown, correctly separating included and not-added-separately items and avoiding double-counting. However, it omits two required line items (section 1459A(a)-(j) grants of $28.5M and Save Our Seas section 302(a) grants of $3.5M) and does not explicitly note that STAG includes non-water items. No prohibited errors were triggered.
