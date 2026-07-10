# E2E Eval Report

## Overall Summary

- **Questions**: 5 (5 scored)
- **Avg Score**: 2.4 / 10
- **Fact Recall**: 23.1%
- **Error Rate**: 4.8%
- **Classify Accuracy**: 40.0%
- **Route Accuracy**: 40.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| general_summary | 5 | 2.4 | 23.1% | 4.8% | 40.0% | 40.0% |

## Per-Question Detail

### summary_1 (score: 6)

**Question**: In plain English, what does the FY2026 Agriculture division do for the FDA?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products
- The FDA Commissioner must submit a detailed obligation plan to the Appropriations Committees within 30 days of enactment

**Judge Reasoning**: The answer covers two of four required facts (FDA salaries/expenses funded and electronic prescribing restriction) but omits the specific user-fee categories and the 30-day obligation plan deadline. No prohibited errors were triggered, and structural rules were followed. Two missing key facts lower the score to 6.

### summary_2 (score: 6)

**Question**: What kinds of projects or activities does the Energy and Water Development division generally support?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- Supported DOE areas include defense environmental cleanup, nuclear energy or atomic energy defense activities, tribal energy, fossil energy research and development, energy efficiency and renewable energy, cybersecurity/energy security/emergency response, electricity and grid deployment, and power administration facilities
- Supported water and civil works activities include hydroelectric facility operations and upgrades
- Supported water activities include Bureau of Reclamation and water storage or restoration projects

**Judge Reasoning**: The answer provides a broad summary of EWD activities, covering both water and energy programs, administrative functions, and cleanup efforts. It correctly avoids ledger formatting and remains within scope. However, it misses several specific DOE areas (energy efficiency/renewable energy, cybersecurity/energy security, power administration) and water activities (hydroelectric, Bureau of Reclamation) required by the gold reference, resulting in incomplete coverage.

### summary_3 (score: 0)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES', 'DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES', 'ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES']
  - Actual: []

**Missed Facts**:
- Water infrastructure appears across USDA, EPA, and Energy-Water
- USDA supports rural water and waste disposal through Rural Utilities Service loans, guarantees, grants, and technical assistance
- EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA
- Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material
- The answer should explain that these are different funding mechanisms and should not be collapsed into a single clean total

**Judge Reasoning**: The final answer is an API error message and contains none of the required facts. It provides no information about water infrastructure across USDA, EPA, and Energy-Water.

### summary_4 (score: 0)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS']
  - Actual: []

**Missed Facts**:
- Regular appropriations provide full-year funding for specified accounts and programs
- Continuing appropriations temporarily extend funding for agencies or accounts without full-year appropriations
- Continuing appropriations generally operate at a prior-year rate for operations
- Continuing appropriations preserve prior-law authority and conditions for continuing projects and activities
- A continuing resolution is not the same as a new full-year line-item appropriation

**Structural Issues**:
- No answer provided; system error prevented any response.

**Judge Reasoning**: The final answer is a pipeline error message with no content related to the question. It provides none of the required facts and fails to address the prompt entirely, resulting in a score of 0.

### summary_5 (score: 0)

**Question**: Summarize what the FY2026 Transportation-HUD division covers for local governments.
**Answer Mode**: expected=general_summary actual= MISMATCH
**Route**: MISMATCH
  - Expected: ['TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES']
  - Actual: []

**Missed Facts**:
- Transportation-HUD covers transportation and housing/urban development programs relevant to local governments
- Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs
- HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs
- The division contains distinct accounts and programs rather than one single local-government funding pool
- The answer should be concise and explanatory rather than a detailed funding ledger

**Triggered Errors**:
- Should not omit either transportation or housing/HUD coverage: Answer is an error message with no coverage of transportation or housing

**Structural Issues**:
- Answer is a pipeline error message with no substantive content

**Judge Reasoning**: The answer is a pipeline error message containing no information about the FY2026 Transportation-HUD division. It fails all required facts and triggers the prohibited error of omitting both transportation and housing coverage. Score 0.
