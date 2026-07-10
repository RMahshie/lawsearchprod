# E2E Eval Report

## Overall Summary

- **Questions**: 3 (3 scored)
- **Avg Score**: 5.3 / 10
- **Fact Recall**: 57.6%
- **Error Rate**: 6.2%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 3 | 5.3 | 57.6% | 6.2% | 100.0% | 100.0% |

## Per-Question Detail

### broad_2 (score: 5)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Tenant-based rental assistance is appropriated $34,438,557,000
- Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025
- Tenant-based rental assistance includes $4,000,000,000 available October 1, 2026
- Tenant-based rental assistance includes $34,957,000,000 for renewals of expiring Section 8 tenant-based annual contributions contracts
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Judge Reasoning**: The answer correctly identifies separate homeless and rental assistance streams and provides many homelessness grant details, but omits the substantial tenant-based rental assistance appropriation and its subcomponents, and fails to mention the Public Housing Fund. Structure is appropriate and no prohibited errors are triggered.

### broad_4 (score: 3)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Local law enforcement, community violence prevention, and police hiring funding is primarily in OJP and COPS
- OJP is $2,400,000,000
- OJP includes $964,000,000 for the Edward Byrne Memorial JAG program
- COPS includes $84,000,000 for police-community relations
- COPS includes $50,000,000 for community violence intervention and prevention
- COPS includes $15,000,000 for de-escalation training
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Triggered Errors**:
- Should not omit either OJP/Byrne JAG or COPS hiring/community violence funding: OJP and Byrne JAG completely missing; COPS community violence intervention ($50M) and police-community relations ($84M) missing

**Structural Issues**:
- Agency/account grouping incomplete: OJP not mentioned, COPS suballocations not all nested under COPS, e.g., community policing development listed separately
- Suballocations not fully nested: $18M community policing development should be under COPS but appears under 'Violence-prevention grants' without clear parent linkage

**Judge Reasoning**: The answer includes some COPS figures (total, hiring, Tribal) and community policing development, but entirely omits OJP and the Byrne JAG program, as well as several COPS sub-programs (police-community relations, community violence intervention, de-escalation training) and the targeted cyber/judicial grants, resulting in major gaps. Additionally, structural nesting and agency grouping are incomplete.

### broad_5 (score: 8)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Judge Reasoning**: The answer accurately lists the major funding amounts, correctly avoids a fabricated total, and follows structural rules. It misses the LUST Trust Fund cleanup subamount and the fee authority note, but no prohibited errors are triggered and the structure is sound. Overall a strong response with minor omissions.
