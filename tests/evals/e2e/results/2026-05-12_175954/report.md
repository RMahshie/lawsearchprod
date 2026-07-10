# E2E Eval Report

## Overall Summary

- **Questions**: 9 (0 scored)
- **Avg Score**: 0.0 / 10
- **Fact Recall**: 0.0%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 0.0%
- **Route Accuracy**: 0.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 2 | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% |
| funding_mechanism_no_amount | 3 | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% |
| general_summary | 2 | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% |
| reconciliation_breakdown | 2 | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% |

## Per-Question Detail

### broad_2 (score: -1)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.

### broad_5 (score: -1)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.

### mechanism_1 (score: -1)

**Question**: How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?
**Answer Mode**: expected=funding_mechanism_no_amount actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.

### mechanism_2 (score: -1)

**Question**: What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?
**Answer Mode**: expected=funding_mechanism_no_amount actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.

### mechanism_5 (score: -1)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.

### recon_3 (score: -1)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.

### recon_4 (score: -1)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.

### summary_3 (score: -1)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES', 'DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES', 'ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.

### summary_4 (score: -1)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.
