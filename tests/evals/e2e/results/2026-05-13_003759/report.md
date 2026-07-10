# E2E Eval Report

## Overall Summary

- **Questions**: 5 (5 scored)
- **Avg Score**: 8.4 / 10
- **Fact Recall**: 84.6%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| general_summary | 5 | 8.4 | 84.6% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### summary_1 (score: 6)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: The answer summarizes FDA funding and key policy limits well, avoids prohibited errors, and follows structural rules. However, it misses required facts about specific user fee categories and the Commissioner's obligation plan deadline, which lowers completeness.

### summary_2 (score: 8)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported water activities include regulatory program activities for navigable waters and wetlands

**Judge Reasoning**: The answer covers most required fact areas comprehensively, with a clear breakdown of EWD programs. However, it omits the required fact about regulatory program activities for navigable waters and wetlands. No prohibited errors were triggered, and the structure adheres to the concise bullet-point format.

### summary_3 (score: 8)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material

**Judge Reasoning**: The answer correctly covers USDA, EPA, and most of Energy-Water, with no prohibited errors and good structure. However, it omits the Bureau of Reclamation and rural water authorization/project material in the Energy-Water division, missing one required fact. Score 8.

### summary_4 (score: 10)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer covers all required facts, avoids all prohibited errors, and follows the structural rules perfectly with concise prose and bullets, no tables, no invented dollar amounts, and appropriate use of CRX tagging.

### summary_5 (score: 10)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer fully meets all requirements: it concisely covers both transportation and housing/HUD programs, mentions distinct program types, avoids dollar totals and account listings, and follows the structural rules with clean bullet points. No errors are triggered.
