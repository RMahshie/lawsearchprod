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
| broad_topic_total | 3 | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% |
| funding_mechanism_no_amount | 2 | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% |
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

### broad_4 (score: -1)

**Question**: What FY2026 funding is available for local law enforcement, community violence prevention, or police hiring?
**Answer Mode**: expected=broad_topic_total actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES']
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

### mechanism_4 (score: -1)

**Question**: Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations mechanism?
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

### recon_1 (score: -1)

**Question**: Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, and explain what sho
**Answer Mode**: expected=reconciliation_breakdown actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES']
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

### summary_3 (score: -1)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES', 'DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES', 'ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.

### summary_5 (score: -1)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES']
  - Actual: []

**Structural Issues**:
- Connection error.

**Judge Reasoning**: Judge error: Connection error.
