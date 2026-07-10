# E2E Eval Report

## Overall Summary

- **Questions**: 2 (2 scored)
- **Avg Score**: 4.5 / 10
- **Fact Recall**: 76.2%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| general_summary | 1 | 3.0 | 25.0% | 0.0% | 100.0% | 100.0% |
| reconciliation_breakdown | 1 | 6.0 | 88.2% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### recon_4 (score: 6)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000
- STAG includes Save Our Seas section 302(a) grants of $3,500,000

**Judge Reasoning**: The answer correctly identifies the STAG total, both SRF pools, and most project-specific grants, with proper structural sections and warnings about double-counting. However, it omits two required facts: the $28,500,000 for SDWA section 1459A(a)-(j) and the $3,500,000 for Save Our Seas section 302(a), instead listing other sections. No prohibited errors are triggered.

### summary_1 (score: 3)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- The FY2026 Agriculture division funds FDA salaries and expenses
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: Only one of four required facts is present (electronic prescribing restriction). The answer misses that the division funds FDA salaries and expenses, lists of user fee types, and the obligation plan requirement. It adds irrelevant details. No prohibited errors or structural issues, but major fact gaps warrant a low score.
