# E2E Eval Report

## Overall Summary

- **Questions**: 4 (4 scored)
- **Avg Score**: 5.0 / 10
- **Fact Recall**: 50.0%
- **Error Rate**: 5.6%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 1 | 6.0 | 62.5% | 20.0% | 100.0% | 100.0% |
| general_summary | 3 | 4.7 | 43.8% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_5 (score: 6)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 104(k) brownfields grants are $98,000,000
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Triggered Errors**:
- Should not omit Hazardous Substance Superfund or brownfields grants: No mention of $98,000,000 brownfields grants under CERCLA section 104(k).

**Judge Reasoning**: The answer correctly identifies most major accounts and warns against summing, but it misses the $98M brownfields grants, the $77.1M Superfund-related activities, and the fee authority. The omission of brownfields grants triggers a prohibited error, and several required facts are absent, though overall structure and treatment of mixed funding are appropriate.

### summary_1 (score: 5)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: The answer covers FDA funding and the electronic prescribing restriction, but omits required facts about user fees and the FDA Commissioner's obligation plan. No prohibited errors were committed and structure follows plain English guidelines.

### summary_2 (score: 4)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water and civil works activities include hydroelectric facility operations and upgrades
- Supported water activities include Bureau of Reclamation and water storage or restoration projects
- Supported water activities include regulatory program activities for navigable waters and wetlands
- Supported cleanup/emergency activities include formerly utilized sites cleanup and flood control or coastal emergencies

**Judge Reasoning**: The answer covers several DOE and water areas but omits critical required facts like fossil energy R&D, power administration, hydroelectric, Bureau of Reclamation, regulatory programs, and formerly utilized sites cleanup, resulting in significant gaps.

### summary_3 (score: 5)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- USDA supports rural water and waste disposal through Rural Utilities Service loans, guarantees, grants, and technical assistance
- Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material

**Judge Reasoning**: The answer correctly covers all three agencies and avoids prohibited errors and structural issues. However, it fails to articulate USDA's loan/guarantee/grant mechanisms and completely omits the Bureau of Reclamation's water projects, which are required facts. These gaps significantly reduce completeness.
