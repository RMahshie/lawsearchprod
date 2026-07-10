# E2E Eval Report

## Overall Summary

- **Questions**: 5 (5 scored)
- **Avg Score**: 6.6 / 10
- **Fact Recall**: 73.1%
- **Error Rate**: 4.8%
- **Classify Accuracy**: 60.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| general_summary | 5 | 6.6 | 73.1% | 4.8% | 60.0% | 100.0% |

## Per-Question Detail

### summary_1 (score: 8)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products

**Judge Reasoning**: The answer covers most required facts clearly in plain English, avoids all prohibited errors, and follows the structural rules. It fails to explicitly mention the full range of user fees that support FDA activities, only noting tobacco user fees and a general preservation of the framework, which is a minor omission.

### summary_2 (score: 2)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=broad_topic_total MISMATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water activities include Bureau of Reclamation and water storage or restoration projects
- The division also funds administration and oversight, including Departmental Administration and the Office of Inspector General

**Triggered Errors**:
- Should not turn the summary into a dollar-by-dollar account ledger: The entire answer is a detailed account-by-account listing with specific dollar amounts, e.g., 'investigations $150,384,000', 'construction $3,169,966,000'.

**Structural Issues**:
- The answer is presented as a dollar-by-dollar account ledger, violating the broad topic summary expectation.
- Amounts lack explicit financial type labels (e.g., direct appropriation, limitation, loan subsidy), which is required when using numbers.
- Though grouped by broad category, the excessive numeric detail undermines the structural goal of a general project/activity summary.

**Judge Reasoning**: The answer provides an inappropriate dollar-by-dollar ledger instead of a general activity summary, triggering a prohibited error. It omits several required program areas (Bureau of Reclamation, energy efficiency/renewable, power administration, cybersecurity, departmental oversight) and focuses on numeric account data rather than broad project types.

### summary_3 (score: 7)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- USDA supports rural water and waste disposal through Rural Utilities Service loans, guarantees, grants, and technical assistance
- EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA

**Judge Reasoning**: The answer successfully summarizes the different treatments across the three agencies and explains that they use distinct mechanisms. However, it omits key details about USDA's use of loans and guarantees and does not mention the EPA's STAG account. These omissions prevent a perfect score but do not detract from the overall clarity.

### summary_4 (score: 10)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=funding_mechanism_no_amount MISMATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly states the difference, covering all required facts: regular appropriations as full-year enacted acts, continuing appropriations as temporary stopgap at prior-year rate, preserving prior-law conditions, and distinguishing them. It avoids prohibited errors by not inventing dollar amounts, not confusing CR with full-year appropriations, including rate-for-operations, and staying within CR mechanics. The structure is compact with a bottom-line and mechanism bullets, matching the mode requirements.

### summary_5 (score: 6)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs

**Judge Reasoning**: The answer effectively summarizes HUD programs for local governments but the transportation coverage is insufficient, omitting major categories like airport and highway funding; overall concise and error-free, but missing a required fact lowers the score.
