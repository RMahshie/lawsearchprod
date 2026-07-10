# E2E Eval Report

## Overall Summary

- **Questions**: 5 (5 scored)
- **Avg Score**: 5.4 / 10
- **Fact Recall**: 46.2%
- **Error Rate**: 4.8%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| general_summary | 5 | 5.4 | 46.2% | 4.8% | 100.0% | 100.0% |

## Per-Question Detail

### summary_1 (score: 3)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment
- The division bars use of funds to implement electronic distribution of prescribing information for certain drugs unless federal law authorizes it

**Triggered Errors**:
- Should not omit the electronic prescribing-information restriction: answer omits any mention of electronic prescribing information restriction

**Judge Reasoning**: The answer covers FDA funding and mentions some activities but omits user fees beyond tobacco, the obligation plan, and the electronic prescribing restriction. It commits the prohibited error of omitting that restriction. Missing three of four required facts leads to a low score.

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
- The division also funds administration and oversight, including Departmental Administration and the Office of Inspector General

**Judge Reasoning**: The answer captures the dual Energy and Water focus but misses most required specifics: it omits tribal energy, energy efficiency, cybersecurity, power administration, hydroelectric upgrades, Bureau of Reclamation, regulatory activities, specific cleanup details, and administrative funding. No structural or prohibited errors.

### summary_3 (score: 7)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material

**Judge Reasoning**: The answer covers most required facts, including the three agency roles and distinct mechanisms, with concise bullets. However, it completely omits Bureau of Reclamation and rural water projects in the Energy-Water section, significantly missing a key piece of the landscape. No prohibited errors are triggered, and structure is fine.

### summary_4 (score: 7)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Regular appropriations provide full-year funding for specified accounts and programs
- Continuing appropriations preserve prior-law authority and conditions for continuing projects and activities
- A continuing resolution is not the same as a new full-year line-item appropriation

**Judge Reasoning**: The answer correctly captures the temporary nature and rate-for-operations of continuing appropriations, but omits two required facts: preservation of prior-law authority and the explicit distinction that a CR is not a new line-item appropriation. No prohibited errors, structure is fine.

### summary_5 (score: 6)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs

**Judge Reasoning**: The answer correctly outlines the general scope of THUD for local governments, covering both transportation and housing/community development, and follows structural rules. However, it fails to mention key HUD-side activities like rental assistance, public housing, and homelessness services as required, which limits completeness.
