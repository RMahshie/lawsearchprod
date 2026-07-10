# E2E Eval Report

## Overall Summary

- **Questions**: 4 (4 scored)
- **Avg Score**: 6.8 / 10
- **Fact Recall**: 77.5%
- **Error Rate**: 5.3%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 1 | 7.0 | 75.0% | 0.0% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 1 | 5.0 | 66.7% | 25.0% | 100.0% | 100.0% |
| general_summary | 1 | 8.0 | 60.0% | 0.0% | 100.0% | 100.0% |
| reconciliation_breakdown | 1 | 7.0 | 85.7% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_5 (score: 7)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Structural Issues**:
- Not explicitly grouped by agency (e.g., EPA vs. DOI) in separate sections; categories are topic-based rather than agency-first
- Some amounts lack explicit financial type labels (e.g., Hazardous Substance Superfund is not labeled as appropriation or trust fund, though LUST is labeled as Trust Fund Program)

**Judge Reasoning**: The answer correctly avoids a false total, lists most key figures, and includes important caveats. It misses the fee authority note and misstates the CERCLA sections for the $77.1M line, but no prohibited errors are triggered and structure is mostly sound with minor agency grouping issues.

### mechanism_5 (score: 5)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Missed Facts**:
- They continue at the FY2025 rate and under the authority and conditions of applicable FY2025 appropriations Acts
- The Act allows certain payments and obligations to continue, including personnel pay and benefits, mandatory payments, essential activities to protect life and property, and orderly termination of government functions

**Triggered Errors**:
- Should not omit the FY2025 rate/authority/conditions concept: the answer never mentions FY2025, only 'applicable appropriations Acts'

**Judge Reasoning**: The answer correctly explains the temporary CR mechanism and most-limited funding concept, but omits the specific FY2025 rate and authority reference, and does not list the allowed payment categories, which are significant fact gaps. The omitted FY2025 concept triggers a prohibited error.

### recon_3 (score: 7)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Direct and guaranteed loan authority total $1,065,000,000
- The two explicitly listed TA/circuit-rider lines total $58,900,000: $35,000,000 rural water and waste technical assistance grants plus $23,900,000 circuit rider
- $4,000,000 is for solid waste management grants

**Judge Reasoning**: The answer correctly separates loan authority, subsidy/grant, and technical assistance lines, avoids all prohibited errors, and follows mode-specific structure. However, it omits the required $4,000,000 solid waste management grants line and does not state two summary totals ($1,065,000,000 combined loan authority and $58,900,000 combined TA/circuit rider), leading to minor factual gaps.

### summary_3 (score: 8)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- USDA supports rural water and waste disposal through Rural Utilities Service loans, guarantees, grants, and technical assistance
- EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA

**Structural Issues**:
- Dollar figures are included for each agency's main accounts, which may not be necessary and could conflict with the request to avoid a detailed dollar breakdown.

**Judge Reasoning**: The answer correctly identifies the three agencies and their distinct approaches to water infrastructure, and clearly states they should not be collapsed into a total. It omits a few specifics from the gold reference, such as USDA's Rural Utilities Service instruments and EPA's targeted border water, and includes some dollar amounts that slightly violate the structural rule, but overall it is a solid summary.
