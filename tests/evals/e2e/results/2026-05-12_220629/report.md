# E2E Eval Report

## Overall Summary

- **Questions**: 4 (4 scored)
- **Avg Score**: 5.5 / 10
- **Fact Recall**: 65.8%
- **Error Rate**: 5.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 3 | 5.3 | 66.7% | 6.2% | 100.0% | 100.0% |
| general_summary | 1 | 6.0 | 60.0% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_2 (score: 7)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Project-based rental assistance is provided $18,143,000,000
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis
- Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding

**Judge Reasoning**: The answer covers most required facts, correctly grouping funding by HUD accounts and nesting suballocations without fabricating a total. However, it omits project-based rental assistance ($18.1B) and the $10M national homeless data analysis, both required facts. No prohibited errors are triggered, and structural rules are followed.

### broad_4 (score: 3)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Local law enforcement, community violence prevention, and police hiring funding is primarily in OJP and COPS
- OJP is $2,400,000,000
- OJP includes $964,000,000 for the Edward Byrne Memorial JAG program
- COPS includes $32,000,000 for Tribal law enforcement hiring and activities
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Triggered Errors**:
- Should not omit either OJP/Byrne JAG or COPS hiring/community violence funding: OJP and Byrne JAG are completely omitted from the answer.

**Structural Issues**:
- Missing OJP agency entirely; funding not grouped by all relevant agencies.
- Amounts not labeled by financial type (e.g., appropriation, grant program).
- COPS suballocations not clearly nested; some listed items (e.g., $20M CRS, $11.5M POLICE Act) may not be COPS subprograms, creating ambiguity.

**Judge Reasoning**: The answer covers COPS and some community violence items but completely omits OJP and its Byrne JAG grants, Tribal law enforcement, and targeted cybercrime/security grants. This violates a key prohibited error and misses several required facts. Structural issues include missing agency groupings, lack of financial type labels, and ambiguous suballocation nesting.

### broad_5 (score: 6)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 128 grants are $46,250,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Structural Issues**:
- Funding not clearly grouped by agency; NIEHS and ANCSA grants lumped as 'other remediation-related grants' under a broad Interior/Environment heading, lacking explicit agency subheadings.
- Financial types inconsistently labeled (e.g., LUST amount described as 'for necessary expenses' but not explicitly as a grant or direct spending; Hazardous Substance Superfund not explicitly typed).
- Suballocations could be more clearly nested under parent accounts (e.g., LUST suballocation for above-ground tanks presented inline but not under an explicit LUST program subheading).

**Judge Reasoning**: The answer correctly separates funding streams and avoids presenting a false total, but it omits CERCLA section 128 grants ($46.25M), the specific $64.583M cleanup suballocation in the LUST program, and the section 3024 fee authority note. Structural grouping is somewhat ad hoc and not fully compliant with mode-specific rules.

### summary_5 (score: 6)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs

**Judge Reasoning**: The answer correctly captures the dual transportation-housing scope but omits key specific programs (e.g., airport/highway/safety grants, rental assistance/public housing). It follows structural rules and avoids prohibited errors, resulting in a moderate factual gap.
