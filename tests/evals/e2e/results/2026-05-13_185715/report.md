# E2E Eval Report

## Overall Summary

- **Questions**: 3 (3 scored)
- **Avg Score**: 6.3 / 10
- **Fact Recall**: 50.0%
- **Error Rate**: 7.7%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 1 | 6.0 | 62.5% | 20.0% | 100.0% | 100.0% |
| general_summary | 2 | 6.5 | 41.7% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_5 (score: 6)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 104(k) brownfields grants are $98,000,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Triggered Errors**:
- Should not omit Hazardous Substance Superfund or brownfields grants: No mention of $98,000,000 brownfields grants under CERCLA section 104(k)

**Structural Issues**:
- Suballocations not nested under parent accounts; e.g., cleanup portion of Leaking Underground Storage Tank Trust Fund ($64,583,000) not broken out under the total.

**Judge Reasoning**: The answer correctly separates accounts and provides many key figures, but it omits the $98M brownfields grants and fails to break out the $64.5M cleanup portion of LUST, and the structural rule about nesting suballocations is not followed. Score 6.

### summary_2 (score: 6)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water and civil works activities include hydroelectric facility operations and upgrades
- Supported water activities include regulatory program activities for navigable waters and wetlands
- Supported cleanup/emergency activities include formerly utilized sites cleanup and flood control or coastal emergencies

**Judge Reasoning**: The answer broadly covers EWD's mix of DOE and water programs, but misses several required specifics like tribal energy, hydroelectric facilities, regulatory activities, and formerly utilized sites cleanup. No prohibited errors and structure is clean, but missing facts limit the score.

### summary_3 (score: 7)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- USDA supports rural water and waste disposal through Rural Utilities Service loans, guarantees, grants, and technical assistance
- EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA
- Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material

**Judge Reasoning**: Answer covers all three agencies, avoids dollar breakdowns and totals, and follows structural rules; but it omits some required specifics (USDA technical assistance, EPA STAG and Alaska/Native Village, Energy-Water rural water projects), causing minor fact gaps.
