# E2E Eval Report

## Overall Summary

- **Questions**: 10 (10 scored)
- **Avg Score**: 7.0 / 10
- **Fact Recall**: 76.6%
- **Error Rate**: 4.3%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 5 | 7.0 | 80.4% | 3.8% | 100.0% | 100.0% |
| general_summary | 5 | 7.0 | 69.2% | 4.8% | 100.0% | 100.0% |

## Per-Question Detail

### broad_1 (score: 6)

**Question**: What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or accounts control it
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- EPA State and Tribal Assistance Grants include Clean Water SRF capitalization grants of $1,638,861,000
- EPA State and Tribal Assistance Grants include Drinking Water SRF capitalization grants of $1,126,101,000
- EPA includes $39,000,000 for Alaska rural and Alaska Native Village drinking water and wastewater infrastructure needs

**Judge Reasoning**: The answer correctly identifies the lack of a single total and provides detailed breakdowns by account, including USDA, EPA, and Reclamation. However, it omits the EPA State and Tribal Assistance Grants SRF capitalization amounts for Clean Water and Drinking Water, and misattributes the Alaska $39M to IHS instead of EPA. All structural rules are followed, and no prohibited errors are triggered. Overall, most facts are present but significant omissions lower the score.

### broad_2 (score: 7)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Project-based rental assistance is provided $18,143,000,000
- Homeless Assistance Grants include $10,000,000 for national homeless data analysis

**Judge Reasoning**: The answer omits two required facts: project-based rental assistance ($18.143B) and the $10M national homeless data analysis amount, which are notable gaps in rental assistance and homelessness specifics. However, it otherwise covers all other facts, avoids prohibited errors, and follows the structural rules effectively.

### broad_3 (score: 10)

**Question**: What FY2026 funding is available for airport infrastructure, runway improvements, or terminal upgrades?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Judge Reasoning**: Answer correctly identifies two THUD airport funding buckets with amounts, nests suballocations without double-counting, and includes runway and terminal examples. It follows all structural rules and avoids prohibited errors.

### broad_4 (score: 8)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program

**Judge Reasoning**: The answer thoroughly covers the funding sources with proper nesting and labeling, meeting all structural rules and containing all required facts except the $7.5M Daniel Anderl grant. No prohibited errors are triggered. The omission of one minor targeted grant keeps it from a perfect score.

### broad_5 (score: 4)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 104(k) brownfields grants are $98,000,000
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Triggered Errors**:
- Should not omit Hazardous Substance Superfund or brownfields grants: brownfields grants (CERCLA section 104(k) $98,000,000) are entirely omitted

**Structural Issues**:
- Suballocations like CERCLA section 128 grants are not nested under their parent account; they appear as top-level 'Key buckets' items instead of being indented or listed within the Superfund account.

**Judge Reasoning**: The answer correctly avoids a clean total and includes Superfund, EPM, and LUST totals, but it omits critical required facts (brownfields grants, cleanup subamounts, sections 311(a)/126(g) funding, fee authority) and triggers a prohibited error by omitting brownfields grants entirely. The structure also lacks proper nesting of suballocations, resulting in major gaps and a low score.

### summary_1 (score: 5)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: The answer covers FDA salaries and expenses funding and the electronic prescribing restriction, but misses two required facts: the specific user fee categories supporting FDA activities and the 30-day obligation plan requirement. It contains no prohibited errors and follows structural rules, but the gap in essential facts significantly reduces completeness.

### summary_2 (score: 6)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water activities include Bureau of Reclamation and water storage or restoration projects
- Supported water activities include regulatory program activities for navigable waters and wetlands
- Supported cleanup/emergency activities include formerly utilized sites cleanup and flood control or coastal emergencies

**Judge Reasoning**: The answer broadly covers DOE and water/civil works but misses several required specifics: tribal energy, Bureau of Reclamation, regulatory activities for navigable waters, and formerly utilized sites cleanup. It avoids prohibited errors and follows structural rules.

### summary_3 (score: 6)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material

**Triggered Errors**:
- Should not provide a detailed dollar-by-dollar breakdown: Clean Water State Revolving Fund capitalization grants of $1,638,861,000 and Drinking Water State Revolving Fund capitalization grants of $1,126,101,000

**Structural Issues**:
- Includes specific dollar amounts for EPA SRF grants, violating the rule to avoid detailed dollar breakdown and the guidance that dollar figures should only appear when directly explaining the answer; the amounts could have been omitted.

**Judge Reasoning**: Answer covers most required facts across USDA, EPA, and Energy-Water with clear distinctions, but omits mention of Bureau of Reclamation under Energy-Water and includes two specific dollar figures despite the instruction to avoid a detailed breakdown. These gaps and minor violations prevent a higher score.

### summary_4 (score: 10)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer covers all required facts concisely, using bullets and no extraneous structure. It clearly distinguishes regular appropriations as full-year annual acts from continuing appropriations as temporary, prior-year-rate stopgaps, with no errors. Perfect adherence to mode-specific rules.

### summary_5 (score: 8)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs

**Judge Reasoning**: The answer effectively summarizes THUD's coverage for local governments, touching on most required facts concisely. It misses explicit mention of highway and safety programs on the transportation side, but otherwise correctly covers both transportation and housing/urban development. No prohibited errors and structure follows mode rules.
