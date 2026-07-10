# E2E Eval Report

## Overall Summary

- **Questions**: 3 (3 scored)
- **Avg Score**: 4.3 / 10
- **Fact Recall**: 52.9%
- **Error Rate**: 0.0%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 66.7%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| general_summary | 3 | 4.3 | 52.9% | 0.0% | 100.0% | 66.7% |

## Per-Question Detail

### summary_2 (score: 7)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported water activities include Bureau of Reclamation and water storage or restoration projects

**Judge Reasoning**: The answer covers nearly all required areas in concise bullets without prohibited errors, but omits the Bureau of Reclamation and water storage/restoration projects, which is a notable gap in the water activities coverage.

### summary_4 (score: 0)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MISMATCH
  - Expected: ['CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS']
  - Actual: []

**Missed Facts**:
- Regular appropriations provide full-year funding for specified accounts and programs
- Continuing appropriations temporarily extend funding for agencies or accounts without full-year appropriations
- Continuing appropriations generally operate at a prior-year rate for operations
- Continuing appropriations preserve prior-law authority and conditions for continuing projects and activities
- A continuing resolution is not the same as a new full-year line-item appropriation

**Judge Reasoning**: The answer completely avoids the question, stating incompatibility and providing no factual content about regular or continuing appropriations. All required facts are missing, resulting in a non-answer.

### summary_5 (score: 6)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs

**Structural Issues**:
- Included specific dollar figures ($62,657,105,821 and $63,396,105,821) that do not directly explain the answer, violating 'Dollar figures only when they directly explain the answer.'

**Judge Reasoning**: The answer covers both transportation and housing/UD programs and lists distinct accounts, satisfying many facts. However, it omits key required elements like airport grants, safety programs, homelessness services, and supportive housing, and includes unnecessary dollar amounts, resulting in a moderate score.
