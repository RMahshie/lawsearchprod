# Embedding Model Eval Report

## Model Summary

| Model | Avg Coverage | Direct % | Adjacent % | Not Responsive % | Judgements |
|-------|-------------|----------|-----------|-----------------|------------|
| text-embedding-3-large | 7.2 | 34.8% | 19.0% | 46.3% | 29 |
| voyage-4-large-2048 | 6.9 | 31.3% | 16.1% | 52.6% | 29 |
| voyage-law-2 | 7.4 | 33.9% | 18.4% | 47.7% | 29 |

## By Question Type

### broad_topic_total

| Model | Avg Coverage | Direct % | Adjacent % | Not Responsive % |
|-------|-------------|----------|-----------|-----------------|
| text-embedding-3-large | 7.0 | 38.1% | 25.0% | 36.9% |
| voyage-4-large-2048 | 6.4 | 31.0% | 22.6% | 46.4% |
| voyage-law-2 | 7.4 | 35.7% | 25.0% | 39.3% |

### direct_account_amount

| Model | Avg Coverage | Direct % | Adjacent % | Not Responsive % |
|-------|-------------|----------|-----------|-----------------|
| text-embedding-3-large | 9.2 | 21.7% | 10.0% | 68.3% |
| voyage-4-large-2048 | 10.0 | 20.0% | 15.0% | 65.0% |
| voyage-law-2 | 9.4 | 18.3% | 25.0% | 56.7% |

### funding_mechanism_no_amount

| Model | Avg Coverage | Direct % | Adjacent % | Not Responsive % |
|-------|-------------|----------|-----------|-----------------|
| text-embedding-3-large | 8.2 | 20.0% | 21.7% | 58.3% |
| voyage-4-large-2048 | 7.2 | 16.7% | 13.3% | 70.0% |
| voyage-law-2 | 8.2 | 18.3% | 11.7% | 70.0% |

### general_summary

| Model | Avg Coverage | Direct % | Adjacent % | Not Responsive % |
|-------|-------------|----------|-----------|-----------------|
| text-embedding-3-large | 4.7 | 45.2% | 21.4% | 33.3% |
| voyage-4-large-2048 | 4.4 | 45.2% | 11.9% | 42.9% |
| voyage-law-2 | 5.0 | 46.4% | 17.9% | 35.7% |

### reconciliation_breakdown

| Model | Avg Coverage | Direct % | Adjacent % | Not Responsive % |
|-------|-------------|----------|-----------|-----------------|
| text-embedding-3-large | 8.2 | 43.3% | 13.3% | 43.3% |
| voyage-4-large-2048 | 7.8 | 38.3% | 16.7% | 45.0% |
| voyage-law-2 | 8.2 | 45.0% | 10.0% | 45.0% |

## Per-Question Detail

### What amount is appropriated for the FDA Salaries and Expenses account in FY2026, and what are the ma...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [AG] | 10 | 4 | 0 | 8 | none |
| voyage-4-large-2048 [AG] | 10 | 3 | 2 | 7 | none |
| voyage-law-2 [AG] | 10 | 4 | 1 | 7 | none |

### What amount is provided for the USDA Food Safety and Inspection Service in FY2026, and what activiti...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [AG] | 10 | 2 | 0 | 10 | none |
| voyage-4-large-2048 [AG] | 10 | 2 | 0 | 10 | none |
| voyage-law-2 [AG] | 10 | 2 | 0 | 10 | none |

### What amount is appropriated for NASA Science in FY2026, and what is the funding available for?

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [CJS] | 8 | 1 | 3 | 8 | The specific purposes for the Science appropriation are not ... |
| voyage-4-large-2048 [CJS] | 10 | 1 | 0 | 11 | none |
| voyage-law-2 [CJS] | 7 | 1 | 8 | 3 | Missing the table referenced in Chunk 0 that specifies sub-a... |

### What amount is appropriated for the EPA Environmental Programs and Management account in FY2026, and...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [INT] | 8 | 2 | 2 | 8 | The full list of specific allocations under the Environmenta... |
| voyage-4-large-2048 [INT] | 10 | 1 | 2 | 9 | none |
| voyage-law-2 [INT] | 10 | 1 | 4 | 7 | none |

### What amount is appropriated for VA Medical Services in FY2026, and what kinds of care or services do...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [MCVA] | 10 | 4 | 1 | 7 | none |
| voyage-4-large-2048 [MCVA] | 10 | 5 | 5 | 2 | none |
| voyage-law-2 [MCVA] | 10 | 3 | 2 | 7 | none |

### What FY2026 funding is available for rural water or wastewater infrastructure, and which agencies or...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [AG] | 9 | 4 | 1 | 7 | Specific Community Project Funding allocations are reference... |
| text-embedding-3-large [INT] | 5 | 4 | 6 | 2 | Missing information on rural water/wastewater funding under ... |
| text-embedding-3-large [EWD] | 4 | 1 | 2 | 9 | Missing specific accounts for rural water and wastewater inf... |
| voyage-4-large-2048 [AG] | 9 | 4 | 1 | 7 | Minor; could potentially miss other minor water/wastewater f... |
| voyage-4-large-2048 [EWD] | 3 | 1 | 3 | 8 | Only one specific rural water project (Northwestern New Mexi... |
| voyage-4-large-2048 [INT] | 5 | 4 | 3 | 5 | Missing total rural water/wastewater funding aggregation wit... |
| voyage-law-2 [AG] | 9 | 4 | 2 | 6 | none |
| voyage-law-2 [EWD] | 2 | 0 | 1 | 11 | No direct appropriation amounts or account details for rural... |
| voyage-law-2 [INT] | 9 | 3 | 8 | 1 | None significant; the key rural-specific water infrastructur... |

### What FY2026 funding is available for a city seeking affordable housing, rental assistance, or homele...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [THUD] | 7 | 8 | 2 | 2 | Missing HOME Investment Partnerships Program funding, a majo... |
| voyage-4-large-2048 [THUD] | 7 | 6 | 4 | 2 | Missing total appropriation for Homeless Assistance Grants; ... |
| voyage-law-2 [THUD] | 7 | 7 | 4 | 1 | Missing total FY2026 appropriation for Homeless Assistance G... |

### What FY2026 funding is available for airport infrastructure, runway improvements, or terminal upgrad...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [THUD] | 8 | 4 | 3 | 5 | The chunks capture the primary funding lanes (two appropriat... |
| voyage-4-large-2048 [THUD] | 9 | 4 | 0 | 8 | none |
| voyage-law-2 [THUD] | 9 | 4 | 1 | 7 | none |

### What FY2026 funding is available for local law enforcement, community violence prevention, or police...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [CJS] | 8 | 4 | 6 | 2 | Minor COPS competitive grants and other sub-accounts may be ... |
| voyage-4-large-2048 [CJS] | 8 | 5 | 3 | 4 | Lacks explicit total for all local law enforcement hiring ac... |
| voyage-law-2 [CJS] | 8 | 5 | 4 | 3 | Some adjacent programs (e.g., bulletproof vests, school safe... |

### What FY2026 funding is available for brownfields cleanup, Superfund cleanup, or environmental remedi...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [INT] | 8 | 7 | 1 | 4 | Missing Leaking Underground Storage Tank Trust Fund appropri... |
| voyage-4-large-2048 [INT] | 4 | 2 | 5 | 5 | Missing explicit total for brownfields cleanup funding; Supe... |
| voyage-law-2 [INT] | 8 | 7 | 1 | 4 | The exact total for the CERCLA grants line in State and Trib... |

### How is Department of Homeland Security funding handled in FY2026, and is there a full-year DHS amoun...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [CRX] | 10 | 3 | 1 | 8 | none |
| voyage-4-large-2048 [CRX] | 8 | 4 | 0 | 8 | None; the chunks provide the generic CR mechanism, DHS-speci... |
| voyage-law-2 [CRX] | 8 | 5 | 1 | 6 | The chunks show DHS is funded via CR at FY2025 rates with sp... |

### What does the Further Continuing Appropriations Act, 2026 do, and what funding mechanism does it use...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [CRX] | 10 | 3 | 2 | 7 | none |
| voyage-4-large-2048 [CRX] | 10 | 2 | 0 | 10 | none |
| voyage-law-2 [CRX] | 9 | 2 | 2 | 8 | None; the two direct chunks together fully explain what the ... |

### How does FY2026 handle FEMA Disaster Relief Fund funding under continuing appropriations?

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [CRX] | 10 | 1 | 4 | 7 | none |
| voyage-4-large-2048 [CRX] | 10 | 1 | 1 | 10 | none |
| voyage-law-2 [CRX] | 8 | 1 | 1 | 10 | General rate-for-operations context is present but no other ... |

### Does the FY2026 text provide a specific dollar amount for CISA, or only a continuing-appropriations ...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [CRX] | 2 | 0 | 2 | 10 | No chunk mentions CISA specifically. Cannot determine from t... |
| voyage-4-large-2048 [CRX] | 0 | 0 | 2 | 10 | No chunk contains any information about CISA funding, either... |
| voyage-law-2 [CRX] | 8 | 1 | 2 | 9 | No chunk explicitly confirms that CISA is covered under the ... |

### What happens to agencies or accounts funded under the continuing resolution if no full-year appropri...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [CRX] | 9 | 5 | 4 | 3 | none |
| voyage-4-large-2048 [CRX] | 8 | 3 | 5 | 4 | Explicit consequences of CR expiration without extension (la... |
| voyage-law-2 [CRX] | 8 | 2 | 1 | 9 | The chunks provide both the termination condition and shutdo... |

### Break down the FY2026 FDA Salaries and Expenses account by FDA center/activity and user-fee source, ...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [AG] | 10 | 5 | 0 | 7 | none |
| voyage-4-large-2048 [AG] | 10 | 4 | 0 | 8 | none |
| voyage-law-2 [AG] | 10 | 5 | 2 | 5 | none |

### Break down NASA FY2026 funding by major account, and explain which amounts can be summed versus whic...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [CJS] | 8 | 7 | 1 | 4 | Missing the explanatory statement tables referenced for Scie... |
| voyage-4-large-2048 [CJS] | 9 | 8 | 1 | 3 | Almost complete; missing detailed subaccount breakdowns with... |
| voyage-law-2 [CJS] | 8 | 7 | 1 | 4 | Missing suballocation details for accounts like Science and ... |

### Break down the USDA Rural Water and Waste Disposal Program Account by loan authority, subsidy/grant ...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [AG] | 9 | 4 | 2 | 6 | none |
| voyage-4-large-2048 [AG] | 9 | 3 | 4 | 5 | External set-asides (REAP and persistent poverty) are mentio... |
| voyage-law-2 [AG] | 8 | 4 | 1 | 7 | Exact amount for REAP set-aside is formula-based, not a fixe... |

### Break down EPA State and Tribal Assistance Grants water infrastructure funding, including SRF capita...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [INT] | 9 | 8 | 3 | 1 | The $41 million sewer overflow grant (Section 221) is water ... |
| voyage-4-large-2048 [INT] | 8 | 6 | 5 | 1 | Possibly missing some smaller water infrastructure project-s... |
| voyage-law-2 [INT] | 9 | 9 | 0 | 3 | The set captures the total STAG appropriation, the SRF capit... |

### Break down IRS FY2026 funding by taxpayer services, enforcement, operations support, and business sy...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [FSGG] | 5 | 2 | 2 | 8 | Missing IRS Business Systems Modernization appropriation; no... |
| voyage-4-large-2048 [FSGG] | 3 | 2 | 0 | 10 | Missing Business Systems Modernization amount; no split betw... |
| voyage-law-2 [FSGG] | 6 | 2 | 2 | 8 | Missing Business Systems Modernization appropriation amount;... |

### In plain English, what does the FY2026 Agriculture division do for the FDA?

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [AG] | 8 | 6 | 0 | 6 | Missing some policy provisions beyond the main funding and a... |
| voyage-4-large-2048 [AG] | 7 | 4 | 0 | 8 | Missing some FDA policy riders and administrative provisions... |
| voyage-law-2 [AG] | 8 | 4 | 0 | 8 | Missing introductory FDA salaries and expenses text and poss... |

### What kinds of projects or activities does the Energy and Water Development division generally suppor...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [EWD] | 7 | 1 | 10 | 1 | No single chunk provides a high-level summary of all divisio... |
| voyage-4-large-2048 [EWD] | 5 | 10 | 0 | 2 | No chunks cover water resource development projects (e.g., A... |
| voyage-law-2 [EWD] | 5 | 3 | 6 | 3 | Missing Bureau of Reclamation water projects, broader Corps ... |

### Summarize how FY2026 appropriations treat water infrastructure across USDA, EPA, and Energy-Water wi...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [AG] | 3 | 5 | 0 | 7 | Only USDA water infrastructure programs are covered; complet... |
| text-embedding-3-large [INT] | 4 | 11 | 1 | 0 | Missing information on USDA water infrastructure programs an... |
| text-embedding-3-large [EWD] | 3 | 10 | 0 | 2 | Only covers Energy-Water division water infrastructure (Corp... |
| voyage-4-large-2048 [AG] | 3 | 6 | 1 | 5 | Only USDA Agriculture division water infrastructure provisio... |
| voyage-4-large-2048 [INT] | 3 | 10 | 0 | 2 | Missing information on USDA water infrastructure (e.g., Rura... |
| voyage-4-large-2048 [EWD] | 8 | 7 | 1 | 4 | Missing USDA and EPA water infrastructure information. EWD c... |
| voyage-law-2 [EWD] | 2 | 8 | 2 | 2 | Chunks only cover the Energy-Water division, with no retriev... |
| voyage-law-2 [AG] | 4 | 4 | 0 | 8 | Missing information from EPA and Energy-Water divisions to p... |
| voyage-law-2 [INT] | 4 | 11 | 1 | 0 | Chunks only cover EPA water infrastructure; no information o... |

### What is the difference between regular appropriations and continuing appropriations in the FY2026 la...

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [CRX] | 3 | 1 | 3 | 8 | Only one chunk directly defines continuing appropriations; n... |
| voyage-4-large-2048 [CRX] | 3 | 1 | 2 | 9 | Retrieved set lacks any description of regular appropriation... |
| voyage-law-2 [CRX] | 7 | 3 | 3 | 6 | The retrieved chunks define continuing appropriations throug... |

### Summarize what the FY2026 Transportation-HUD division covers for local governments.

| Model | Coverage | Direct | Adjacent | Not Resp. | Gaps |
|-------|----------|--------|----------|-----------|------|
| text-embedding-3-large [THUD] | 5 | 4 | 4 | 4 | Missing broad coverage of major formula grant programs for l... |
| voyage-4-large-2048 [THUD] | 2 | 0 | 6 | 6 | No summaries or comprehensive listings of local government p... |
| voyage-law-2 [THUD] | 5 | 6 | 3 | 3 | Missing major HUD block grants like CDBG and HOME, and no ov... |
