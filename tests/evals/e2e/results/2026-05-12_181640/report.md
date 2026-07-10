# E2E Eval Report

## Overall Summary

- **Questions**: 9 (8 scored)
- **Avg Score**: 7.5 / 10
- **Fact Recall**: 76.9%
- **Error Rate**: 5.1%
- **Classify Accuracy**: 100.0%
- **Route Accuracy**: 100.0%

## By Answer Mode

| Mode | Count | Avg Score | Fact Recall | Error Rate | Classify | Route |
|------|-------|-----------|-------------|------------|----------|-------|
| broad_topic_total | 2 | 6.5 | 72.7% | 9.1% | 100.0% | 100.0% |
| funding_mechanism_no_amount | 3 | 10.0 | 100.0% | 0.0% | 100.0% | 100.0% |
| general_summary | 2 | 7.0 | 80.0% | 12.5% | 100.0% | 100.0% |
| reconciliation_breakdown | 2 | 6.5 | 73.7% | 0.0% | 100.0% | 100.0% |

## Per-Question Detail

### broad_2 (score: 8)

**Question**: What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homelessness services?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- Tenant-based rental assistance includes $4,000,000,000 previously appropriated and available October 1, 2025
- Tenant-based rental assistance includes $4,000,000,000 available October 1, 2026
- Youth homelessness system improvement grants may receive up to $25,000,000

**Judge Reasoning**: The answer correctly identifies the THUD funding streams, separates rental assistance, public housing, and homelessness, and avoids presenting a single total. It includes all major amounts and protects against key errors. Minor omissions: specific advance appropriation dates and the $25M youth homelessness improvement sub-grant are missing. Overall strong compliance.

### broad_5 (score: 5)

**Question**: What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remediation?
**Answer Mode**: expected=broad_topic_total actual=broad_topic_total MATCH
**Route**: MATCH

**Missed Facts**:
- CERCLA section 104(k) brownfields grants are $98,000,000
- Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000
- EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided

**Triggered Errors**:
- Should not omit Hazardous Substance Superfund or brownfields grants: omits CERCLA §104(k) brownfields grants of $98,000,000

**Structural Issues**:
- State and Tribal Assistance Grants remediation projects listed top-level instead of nested under STAG account
- some amounts lack clear parent account nesting (e.g., remediation of above ground leaking fuel tanks)
- grouping by agency but mixing account and program lines could be clearer

**Judge Reasoning**: Answer correctly notes no clean total, lists Superfund, LUST, section 128 grants, and EPM. However, it omits the $98M CERCLA §104(k) brownfields grants and the $77.1M Superfund-related activities under §311(a) and §126(g), and does not mention the CERCLA §3024 fee authority. It does not present an additive total and avoids mischaracterizing EPM, but the omission of brownfields grants is a significant gap. Structure partially groups by agency but some suballocations are not nested.

### mechanism_1 (score: 10)

**Question**: How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amount in these laws?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly explains DHS funding via continuing appropriations with rate-for-operations, cites extension dates, explicitly states no full-year amount, and adheres to the compact structural rules.

### mechanism_2 (score: 10)

**Question**: What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Judge Reasoning**: The answer correctly identifies the Act as a continuing resolution, explains the rate-for-operations mechanism, avoids inventing a total, and follows all structural rules concisely.

### mechanism_5 (score: -1)

**Question**: What happens to agencies or accounts funded under the continuing resolution if no full-year appropriation is provided?
**Answer Mode**: expected=funding_mechanism_no_amount actual=funding_mechanism_no_amount MATCH
**Route**: MATCH

**Structural Issues**:
- Expecting ',' delimiter: line 11 column 116 (char 570)

**Judge Reasoning**: Judge error: Expecting ',' delimiter: line 11 column 116 (char 570)

### recon_3 (score: 5)

**Question**: Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant funding, technical a
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- The two explicitly listed TA/circuit-rider lines total $58,900,000: $35,000,000 rural water and waste technical assistance grants plus $23,900,000 circuit rider
- $1,000,000 is for rural utilities program under section 306(a)(2)(B)
- $5,000,000 is for section 306E rural utilities activity
- $1,000,000 within section 306E is for subgrants for household decentralized wastewater systems
- $7,000,000 is for section 306A(i)(2) grants
- $60,000,000 is for loans and grants including water and waste disposal systems grants and Native/tribal/Hawaiian Home Lands purposes
- $23,900,000 is for the circuit rider program
- $4,000,000 is for solid waste management grants

**Judge Reasoning**: The answer correctly identifies major categories, avoids all prohibited errors, and follows structural rules with Included and Not Added Separately sections. However, it omits many required line items from the gold reference (e.g., $23.9M circuit rider, $60M, $7M, $4M, several $1M items), resulting in significant fact gaps and an incomplete breakdown.

### recon_4 (score: 8)

**Question**: Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capitalization grants and 
**Answer Mode**: expected=reconciliation_breakdown actual=reconciliation_breakdown MATCH
**Route**: MATCH

**Missed Facts**:
- EPA State and Tribal Assistance Grants account totals $4,409,609,000
- STAG includes Save Our Seas section 302(a) grants of $3,500,000

**Judge Reasoning**: The answer correctly breaks down water infrastructure funding with included components and avoids double-counting. However, it does not mention the overall STAG account total ($4.4B) and omits the Save Our Seas grant (instead listing FWPCA section 124), so two required facts are missing.

### summary_3 (score: 5)

**Question**: Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water without doing a detail
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Missed Facts**:
- EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA
- The answer should explain that these are different funding mechanisms and should not be collapsed into a single clean total

**Triggered Errors**:
- Should not provide a detailed dollar-by-dollar breakdown: Multiple specific dollar amounts are listed: $1,015,000,000 for USDA direct loans, $50,000,000 for guaranteed loans, $445,864,564 for USDA cost, $35,000,000 and $23,900,000 for technical assistance, $1,638,861,000 and $1,126,101,000 for EPA SRFs, $64,634,000 for WIFIA, $221,000,000 and $40,000,000 for Corps, and authorization level changes.

**Structural Issues**:
- Dollar figures are used extensively throughout the answer, contradicting the instruction to avoid a detailed dollar breakdown and the rule that dollar figures should appear only when they directly explain the answer.

**Judge Reasoning**: The answer correctly identifies the three agencies and broadly captures their water infrastructure activities, but it violates the prohibition against a detailed dollar breakdown by including numerous specific figures. Additionally, it omits key EPA categories (STAG, border, Alaska) and fails to explicitly caution against collapsing the different funding mechanisms into a single total. These gaps and errors limit the score to 5.

### summary_4 (score: 9)

**Question**: What is the difference between regular appropriations and continuing appropriations in the FY2026 laws?
**Answer Mode**: expected=general_summary actual=general_summary MATCH
**Route**: MATCH

**Judge Reasoning**: The answer accurately covers all required facts in concise prose, clearly distinguishing regular from continuing appropriations. The rate‑for‑operations concept is mentioned, though a direct 'prior‑year' link is absent but acceptable given the legal phrasing. No errors were triggered and all structural rules were followed.
