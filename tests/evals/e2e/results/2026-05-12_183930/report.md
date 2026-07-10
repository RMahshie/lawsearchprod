# E2E Eval Report

## Overall Summary

- **Questions**: 4 (4 scored)
- **Avg Score**: 5.0 / 10
- **Fact Recall**: 72.5%
- **Error Rate**: 5.3%
- **Classify Accuracy**: 50.0%
- **Route Accuracy**: 75.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 1 | 6.0 | 62.5% | 0.0% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 1 | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% |
| general_summary | 1 | 6.0 | 100.0% | 25.0% | 0.0% | 100.0% |
| reconciliation_breakdown | 1 | 8.0 | 90.5% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_5 (score: 6)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Structural Issues**:
- Missing required suballocation for Superfund-related activities ($77,100,000).
- Leaking Underground Storage Tank amount lacks breakdown of cleanup-specific portion ($64,583,000), implying entire amount is for cleanup.
- Amounts not consistently labeled with financial type (e.g., grants vs. appropriations).

**Judge Reasoning**: The answer correctly identifies key accounts and avoids aggregating mixed funding types. It covers most major remediation amounts but omits the $77.1M Superfund-related activities and the LUST cleanup breakdown. Structural issues include missing suballocations and inconsistent financial type labels. No prohibited errors were committed.

### mechanism_5 (score: 0)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS']
  - Actual: []

**Missed Facts**:
- Agencies or accounts without full-year appropriations continue operating under the continuing resolution
- They continue at the FY2025 rate and under the authority and conditions of applicable FY2025 appropriations Acts
- The continuation applies to continuing projects and activities through the date specified in section 106(3)
- They may continue only at the most limited funding action permitted
- The Act allows certain payments and obligations to continue, including personnel pay and benefits, mandatory payments, essential activities to protect life and property, and orderly termination of government functions
- Payments and reimbursements are made only to the extent and in the amounts provided in advance in appropriations Acts

**Structural Issues**:
- The answer is a system error message and does not provide any substantive response to the question.

**Judge Reasoning**: The final answer consists entirely of a pipeline error and contains none of the required facts. It does not address the question at all, so it fails completely to meet the gold standard.

### recon_3 (score: 8)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Direct and guaranteed loan authority total $1,065,000,000
- The two explicitly listed TA/circuit-rider lines total $58,900,000: $35,000,000 rural water and waste technical assistance grants plus $23,900,000 circuit rider

**Judge Reasoning**: The answer correctly breaks down the account, separating included amounts from suballocations and transfers, with accurate financial labeling. It covers all required numbers and avoids prohibited errors. However, it does not explicitly state the combined loan authority total ($1,065,000,000) or the total technical assistance/circuit rider amount ($58,900,000), which were required facts. Thus, score 8.

### summary_3 (score: 6)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=broad_topic_total MISMATCH
**Route**: MATCH

**Triggered Errors**:
- Should not provide a detailed dollar-by-dollar breakdown: The answer includes many specific dollar amounts, e.g., '$445,864,564', '$1,015,000,000', '$4,409,609,000', '$1,638,861,000', etc., providing a detailed breakdown.

**Judge Reasoning**: The answer correctly identifies the cross-agency treatment and highlights that a single total is not feasible, fulfilling all required facts. However, it includes a detailed dollar-by-dollar breakdown (many specific amounts) that violates the user’s explicit instruction and a prohibited error, preventing a higher score.
