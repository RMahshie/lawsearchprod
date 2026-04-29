# FY2026 Corpus Conversion

## Goal
Convert LawSearch into a FY2026-only product by updating ingestion, routing, validation, and manual division selection around the 2026 public-law bill structure in `data/bills/2026`.

The implementation should build one active FY2026 vector-store generation from explicit FY2026 configuration, including a routable catch-all store for continuing appropriations, extenders, Homeland Security-related continuation/extender material, and other matters.

## Non-Goals
- Do not preserve 2024 query routing or manual filter compatibility.
- Do not change saved conversation history behavior; old rows may remain visible until the user deletes old DB data manually.
- Do not support user-selectable corpus years in the API or UI.
- Do not delete old 2024 source files, Chroma stores, saved conversations, or registry rows as part of this work.
- Do not add a fake FY2026 annual appropriations division for Homeland Security.
- Do not add year/corpus switching.
- Do not add extra source metadata or UI fields beyond what is needed for FY2026 source display.

## Current Behavior
The app currently assumes a flat mapping from division name to Chroma store directory in `settings.subcommittee_stores`.

Ingestion infers the source bill file and division letter from each Chroma store directory name. That works for the 2024 structure but is too brittle for FY2026, where routable divisions are spread across three source files and the catch-all store combines multiple source divisions from two public laws.

Routing builds its allowed division list from `settings.subcommittee_stores`. Manual `divisions_filter` validation and the frontend division checklist also use hard-coded 2024 division names. Saved source hydration loads chunks by `vector_store_id + division + chunk_id`, and currently relies on the active code's configured division mapping.

## Fresh Context Handoff
This plan is intended to be enough for a new thread with no prior chat context. The user has already approved the FY2026-only conversion, the routable division set, the catch-all label/acronym, the store names, the routing aliases, and the implementation boundaries below.

Repo facts to preserve:
- Use `python3`, not bare `python`.
- Required env is `OPENAI_API_KEY`; optional env is `DEBUG`.
- For complex work, keep this plan updated while implementing.
- Make small logical commits as sections finish, with no assistant attribution or co-author trailers.
- The user will run real ingestion and paste errors/logs; do not require Codex to run live ingestion.

Implementation boundaries:
- Do not add corpus/year switching.
- Do not preserve 2024 routing/filter compatibility.
- Do not delete old 2024 files, DB rows, Chroma stores, or saved conversations.
- Do not change saved conversation history filtering.
- Do not change storage manager filtering.
- Do not add broad new metadata/UI for normal divisions.
- Keep the implementation close to the current 2024 structure; do not introduce a large new corpus abstraction unless implementation proves the existing structure cannot support FY2026.

## Proposed Behavior
Keep the same general 2024 configuration style: `settings.subcommittee_stores` remains the app's canonical division-name-to-Chroma-store mapping. Add the minimum additional FY2026 configuration needed for ingestion to resolve source files and division letters without parsing store names.

Each FY2026 configured division should include the canonical route label, Chroma store directory name, source file, source division letter or letters, routing aliases, and acronym.

FY2026 routable divisions:
- `AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES`
- `LEGISLATIVE BRANCH`
- `MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES`
- `COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES`
- `ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES`
- `DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES`
- `DEPARTMENT OF DEFENSE`
- `DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES`
- `TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES`
- `FINANCIAL SERVICES AND GENERAL GOVERNMENT`
- `DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS`
- `CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS`

Use `CRX` as the source badge acronym for the catch-all division.

Store directory naming rule: use the source filename stem plus the division name, sanitized/normalized in the existing uppercase underscore style. Preserve the `Division_<letter>` portion for normal divisions.

Use these exact FY2026 store directory names:
- `AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES`: `FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS_Division_B_AGRICULTURE_RURAL_DEVELOPMENT_FOOD_AND_DRUG_ADMINISTRATION_AND_RELATED_AGENCIES`
- `LEGISLATIVE BRANCH`: `FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS_Division_C_LEGISLATIVE_BRANCH`
- `MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES`: `FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS_Division_D_MILITARY_CONSTRUCTION_VETERANS_AFFAIRS_AND_RELATED_AGENCIES`
- `COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES`: `FY2026_COMMERCEJUSTICESCIENCE_ENERGYWATERDEV_INTERIORENVIRONMENTAL_Division_A_COMMERCE_JUSTICE_SCIENCE_AND_RELATED_AGENCIES`
- `ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES`: `FY2026_COMMERCEJUSTICESCIENCE_ENERGYWATERDEV_INTERIORENVIRONMENTAL_Division_B_ENERGY_AND_WATER_DEVELOPMENT_AND_RELATED_AGENCIES`
- `DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES`: `FY2026_COMMERCEJUSTICESCIENCE_ENERGYWATERDEV_INTERIORENVIRONMENTAL_Division_C_DEPARTMENT_OF_THE_INTERIOR_ENVIRONMENT_AND_RELATED_AGENCIES`
- `DEPARTMENT OF DEFENSE`: `FY2026_CONSOLIDATED_Division_A_DEPARTMENT_OF_DEFENSE`
- `DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES`: `FY2026_CONSOLIDATED_Division_B_DEPARTMENTS_OF_LABOR_HEALTH_AND_HUMAN_SERVICES_AND_EDUCATION_AND_RELATED_AGENCIES`
- `TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES`: `FY2026_CONSOLIDATED_Division_D_TRANSPORTATION_HOUSING_AND_URBAN_DEVELOPMENT_AND_RELATED_AGENCIES`
- `FINANCIAL SERVICES AND GENERAL GOVERNMENT`: `FY2026_CONSOLIDATED_Division_E_FINANCIAL_SERVICES_AND_GENERAL_GOVERNMENT`
- `DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS`: `FY2026_CONSOLIDATED_Division_F_DEPARTMENT_OF_STATE_FOREIGN_OPERATIONS_AND_RELATED_PROGRAMS`
- `CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS`: `FY2026_OTHER_CONTINUING_APPROPRIATIONS_EXTENDERS_HOMELAND_SECURITY_OTHER_MATTERS`

Use this exact catch-all store directory name:
- `FY2026_OTHER_CONTINUING_APPROPRIATIONS_EXTENDERS_HOMELAND_SECURITY_OTHER_MATTERS`

The catch-all store should combine:
- P.L. 119-37 Division A, Continuing Appropriations Act, 2026
- P.L. 119-37 Division E, Extension of Agricultural Programs
- P.L. 119-37 Division F, Health Extenders
- P.L. 119-37 Division G, Department of Veterans Affairs Extenders
- P.L. 119-37 Division H, Miscellaneous
- P.L. 119-75 Division G, Other Matters
- P.L. 119-75 Division H, Further Continuing Appropriations Act, 2026
- P.L. 119-75 Division I, Authorizing Extenders and Technical Corrections
- P.L. 119-75 Division J, Health Care Extenders

Use these exact source files and division parts:
- `AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES`
  - source file: `data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm`
  - public law label: `P.L. 119-37`
  - source division letter: `B`
  - source division title: `Agriculture, Rural Development, Food and Drug Administration, and Related Agencies Appropriations Act, 2026`
- `LEGISLATIVE BRANCH`
  - source file: `data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm`
  - public law label: `P.L. 119-37`
  - source division letter: `C`
  - source division title: `Legislative Branch Appropriations Act, 2026`
- `MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES`
  - source file: `data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm`
  - public law label: `P.L. 119-37`
  - source division letter: `D`
  - source division title: `Military Construction, Veterans Affairs, and Related Agencies Appropriations Act, 2026`
- `COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES`
  - source file: `data/bills/2026/FY2026_CommerceJusticeScience_EnergyWaterDev_INTERIOREnvironmental.htm`
  - public law label: `P.L. 119-74`
  - source division letter: `A`
  - source division title: `Commerce, Justice, Science, and Related Agencies Appropriations Act, 2026`
- `ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES`
  - source file: `data/bills/2026/FY2026_CommerceJusticeScience_EnergyWaterDev_INTERIOREnvironmental.htm`
  - public law label: `P.L. 119-74`
  - source division letter: `B`
  - source division title: `Energy and Water Development and Related Agencies Appropriations Act, 2026`
- `DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES`
  - source file: `data/bills/2026/FY2026_CommerceJusticeScience_EnergyWaterDev_INTERIOREnvironmental.htm`
  - public law label: `P.L. 119-74`
  - source division letter: `C`
  - source division title: `Department of the Interior, Environment, and Related Agencies Appropriations Act, 2026`
- `DEPARTMENT OF DEFENSE`
  - source file: `data/bills/2026/FY2026_CONSOLIDATED.htm`
  - public law label: `P.L. 119-75`
  - source division letter: `A`
  - source division title: `Department of Defense Appropriations Act, 2026`
- `DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES`
  - source file: `data/bills/2026/FY2026_CONSOLIDATED.htm`
  - public law label: `P.L. 119-75`
  - source division letter: `B`
  - source division title: `Departments of Labor, Health and Human Services, and Education, and Related Agencies Appropriations Act, 2026`
- `TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES`
  - source file: `data/bills/2026/FY2026_CONSOLIDATED.htm`
  - public law label: `P.L. 119-75`
  - source division letter: `D`
  - source division title: `Transportation, Housing and Urban Development, and Related Agencies Appropriations Act, 2026`
- `FINANCIAL SERVICES AND GENERAL GOVERNMENT`
  - source file: `data/bills/2026/FY2026_CONSOLIDATED.htm`
  - public law label: `P.L. 119-75`
  - source division letter: `E`
  - source division title: `Financial Services and General Government Appropriations Act, 2026`
- `DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS`
  - source file: `data/bills/2026/FY2026_CONSOLIDATED.htm`
  - public law label: `P.L. 119-75`
  - source division letter: `F`
  - source division title: `National Security, Department of State, and Related Programs Appropriations Act, 2026`
- `CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS`
  - source file: `data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm`, public law label: `P.L. 119-37`, source division letter: `A`, source division title: `Continuing Appropriations Act, 2026`
  - source file: `data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm`, public law label: `P.L. 119-37`, source division letter: `E`, source division title: `Extension of Agricultural Programs`
  - source file: `data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm`, public law label: `P.L. 119-37`, source division letter: `F`, source division title: `Health Extenders`
  - source file: `data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm`, public law label: `P.L. 119-37`, source division letter: `G`, source division title: `Department of Veterans Affairs Extenders`
  - source file: `data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm`, public law label: `P.L. 119-37`, source division letter: `H`, source division title: `Miscellaneous`
  - source file: `data/bills/2026/FY2026_CONSOLIDATED.htm`, public law label: `P.L. 119-75`, source division letter: `G`, source division title: `Other Matters`
  - source file: `data/bills/2026/FY2026_CONSOLIDATED.htm`, public law label: `P.L. 119-75`, source division letter: `H`, source division title: `Further Continuing Appropriations Act, 2026`
  - source file: `data/bills/2026/FY2026_CONSOLIDATED.htm`, public law label: `P.L. 119-75`, source division letter: `I`, source division title: `Authorizing Extenders and Technical Corrections`
  - source file: `data/bills/2026/FY2026_CONSOLIDATED.htm`, public law label: `P.L. 119-75`, source division letter: `J`, source division title: `Health Care Extenders`

Ingestion should fail loudly if a configured source file is missing, an expected division header is not found, or extracted text is suspiciously small. It should not silently ingest a full file as a substitute for a missing division.

Suspiciously-small guard: after extraction and chunking, each configured source part must produce at least 2 chunks with the configured chunk size/overlap. If any source part produces fewer than 2 chunks, abort ingestion with a clear error naming the canonical division, source file, source division letter, and extracted character count. This guard exists to expose regex/header extraction bugs early.

Routing should expose only the FY2026 routable divisions. The routing prompt should include exact allowed division labels plus these explicit aliases and routing hints:
- `AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES`: agriculture, USDA, rural development, FDA, food and drug, food safety, farm programs, nutrition programs, WIC, SNAP references when tied to agriculture appropriations.
- `LEGISLATIVE BRANCH`: Congress, House, Senate, Capitol Police, Architect of the Capitol, Library of Congress, Government Accountability Office, GAO, Congressional Budget Office, CBO.
- `MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES`: military construction, MILCON, veterans affairs, VA, veterans health, veterans benefits, cemeteries, American Battle Monuments Commission.
- `COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES`: CJS, Commerce, DOJ, Justice, FBI, DEA, ATF, prisons, NASA, NSF, NOAA, Census, NIST, science agencies.
- `ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES`: Energy and Water, Department of Energy, DOE, Corps of Engineers, Bureau of Reclamation, water projects, nuclear security, NNSA.
- `DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES`: Interior, DOI, EPA, environment, public lands, National Park Service, Bureau of Land Management, Fish and Wildlife, Indian Affairs, Forest Service, Smithsonian.
- `DEPARTMENT OF DEFENSE`: Defense, DOD, military personnel, operation and maintenance, procurement, research and development, RDT&E, Army, Navy, Marine Corps, Air Force, Space Force.
- `DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES`: Labor, DOL, HHS, Education, ED, NIH, CDC, CMS, public health, schools, Pell, student aid, workforce, OSHA.
- `TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES`: THUD, Transportation, DOT, FAA, highways, transit, rail, maritime, HUD, housing, rental assistance, community development.
- `FINANCIAL SERVICES AND GENERAL GOVERNMENT`: FSGG, Treasury, IRS, Executive Office of the President, judiciary, District of Columbia, GSA, OPM, SEC, FCC, FTC, SBA.
- `DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS`: State, foreign operations, SFOPS, diplomacy, embassy, USAID, foreign assistance, international security assistance, export/import, Peace Corps.
- `CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS`: CR, continuing resolution, continuing appropriations, extensions, extenders, technical corrections, Homeland Security, DHS, FEMA, cybersecurity, E-Verify, H-2B, National Flood Insurance Program, NFIP, health care extenders, Medicare extenders, Medicaid extenders, VA extenders, other matters.

If routing returns no valid FY2026 division, do not query all divisions. End the graph with exactly this final answer: `This question is incompatible with the FY2026 appropriations text available in LawSearch.` The response text should be implemented as a constant and covered by a unit test.

The frontend manual division checklist should be updated to the static FY2026 list. Old 2024 division names should not appear in validation, routing, or frontend choices.

Do not change saved conversation history behavior in this implementation. Old DB rows may remain visible until the user deletes old DB data manually.

Do not change storage manager behavior in this implementation. Old storage rows/artifacts may remain visible until the user deletes old DB data manually.

For normal divisions, do not add extra source metadata unless the existing source display path needs it. For catch-all chunks, preserve metadata for the original public law and original source division so source hovers/cards can show the original division while indicating the source is grouped under the `CRX` catch-all bucket.

Use these metadata keys for CRX chunks:
- `source_public_law`: short label such as `P.L. 119-75`
- `source_division_letter`: original division letter such as `H`
- `source_division_title`: original division title such as `Further Continuing Appropriations Act, 2026`
- `source_bucket`: `CRX`

Visible CRX source display requirement: source cards and source/number popovers for `CRX` chunks should include a compact line using short public-law labels, such as `Original division: P.L. 119-75 Division H - Further Continuing Appropriations Act, 2026`. Do not add this line for non-CRX sources.

## Relevant Files
- `app/core/config.py`
- `app/services/ingestion_service.py`
- `app/services/vector_store_service.py`
- `app/services/rag_service.py`
- `app/models/query.py`
- `frontend/src/types/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/QueryResults.tsx`
- `.agents/plans/fy2026-corpus-conversion.md`
- `tests/test_ingestion_service.py`
- `tests/test_query_models.py`
- `tests/test_rag_service_units.py`
- `data/bills/2026/`

## Assumptions
- FY2026 replaces FY2024 for this branch.
- Existing 2024 files and vector-store rows can remain on disk/in the DB, but they are unsupported for new query behavior.
- A new FY2026 vector-store generation will be ingested and activated after the code changes.
- Existing APIs can keep their current request/response shapes unless implementation discovers a hard blocker.
- The user will run real FY2026 ingestion and paste errors/logs; implementation should not require Codex to run the ingestion smoke test.
- If the implementation discovers that one of the listed public-law labels or source titles disagrees with the actual file text, update this plan under Discoveries before changing behavior.

## Open Questions
- None.

## Execution Steps
- [x] Update `settings.subcommittee_stores` to the FY2026 division-to-store mapping.
- [x] Add minimal FY2026 source-part configuration in the same configuration style as the current 2024 setup.
- [x] Use the exact source file/division/public-law/title mapping listed in this plan.
- [x] Replace 2024 `subcommittee_stores` defaults and division acronym defaults with FY2026 entries, including `CRX`.
- [x] Rework ingestion to read manifest entries instead of inferring bill paths and letters from store names.
- [x] Preserve the current body-header extraction strategy unless tests prove the FY2026 HTML requires a different approach.
- [x] Add strict extraction validation for missing files, missing headers, and any configured source part producing fewer than 2 chunks.
- [x] Build one Chroma directory per routable division.
- [x] Build catch-all ingestion by extracting all configured source parts and chunking them into one canonical `CRX` division store while preserving original public-law/source-division metadata on chunks.
- [x] Update vector-store retrieval and chunk hydration to resolve FY2026 store names from the manifest-backed mapping.
- [x] Update route selection and route prompt context so the router sees exact FY2026 labels plus the explicit aliases listed in this plan.
- [x] Replace the current "query all divisions" router fallback with the incompatible-question answer path.
- [x] Update `QueryRequest.divisions_filter` validation to use the FY2026 division set.
- [x] Update the frontend static `AVAILABLE_DIVISIONS` list to FY2026.
- [x] Do not change saved conversation history filtering or direct saved-conversation detail behavior.
- [x] Do not change storage manager filtering.
- [x] Add the CRX-only original division line in source cards/popovers.
- [x] Update this plan after each meaningful implementation step, including changed files, decisions, discoveries, validation, and remaining work.
- [x] Convert existing 2024-focused tests to FY2026 coverage instead of keeping dual-corpus tests.
- [x] Make small logical commits as sections of work are completed, without assistant attribution or co-author trailers.
- [x] Update the plan's Progress, Decisions, Discoveries, and Remaining Work sections during implementation.

## Validation
Run focused backend checks:

```bash
python3 -m pytest tests/test_ingestion_service.py tests/test_rag_service_units.py tests/test_query_models.py
```

Run frontend build validation:

```bash
npm run build:frontend
```

After ingestion is available, perform a manual smoke check with `DEBUG=true`:
- User ingests and activates a FY2026 vector store, then provides errors/logs if ingestion fails.
- Ask an Agriculture/FDA question and verify routing to `AG`.
- Ask a DOD question and verify routing to `DOD`.
- Ask a DHS/FEMA/cybersecurity continuation or extender question and verify routing to `CRX`.
- Confirm retrieved source chunks have persisted `chunk_id`s.
- Confirm catch-all source display identifies the original source division.

## Documentation
- Update `AGENTS.md` only for non-obvious durable FY2026-specific invariants that would take future agents meaningful investigation to rediscover.
- Update API/UI docs only if request/response shapes or visible division names are documented elsewhere.
- Avoid documenting obvious file maps that future agents can infer by reading the code.

## Progress
- 2026-04-29: Plan created from architecture review and user decisions. No implementation started.
- 2026-04-29: Incorporated user decisions on FY2026-only behavior, config style, routing fallback, source metadata scope, history/storage treatment, tests, validation ownership, and commit workflow. No implementation started.
- 2026-04-29: Added fresh-thread handoff context, exact source file/division mapping, and CRX metadata keys. No implementation started.
- 2026-04-29: Implemented FY2026 constants and manifest-backed defaults in `app/core/config.py`, switched division acronyms to FY2026 including `CRX`, and added the exact FY2026 source files under `data/bills/2026/`.
- 2026-04-29: Reworked `app/services/ingestion_service.py` to ingest from configured source parts, fail on missing files/headers/suspiciously small source parts, and combine all CRX source parts into one routable store with original source metadata.
- 2026-04-29: Updated routing in `app/services/rag_service.py` to present exact FY2026 labels with the approved aliases and to return the incompatible-question answer instead of querying every division when routing has no valid FY2026 division.
- 2026-04-29: Updated API validation/examples, frontend manual division choices, README corpus wording, and CRX-only original-division display in relevant source cards/popovers.
- 2026-04-29: Converted focused backend tests to FY2026 behavior and added coverage for FY2026 routing aliases, incompatible routing, FY2026 extraction, and CRX metadata.
- 2026-04-29: Validation passed: `python3 -m pytest tests/test_ingestion_service.py tests/test_rag_service_units.py tests/test_query_models.py` reported 38 passed; `npm run build:frontend` completed successfully with existing Vite font-resolution and chunk-size warnings.
- 2026-04-29: Created logical commits `ccced49` (`Convert backend to FY2026 corpus`) and `f5af7c1` (`Update FY2026 division UI`) without assistant attribution or co-author trailers.

## Decisions
- FY2026 is the only supported product corpus for this branch.
- The catch-all division is routable and canonicalized as `CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS`.
- The catch-all source badge acronym is `CRX`.
- Ingestion should fail loudly rather than falling back to full-file ingestion or skipping expected divisions.
- Frontend manual filters should use a static FY2026 list for this change.
- Store directory names should be sanitized/normalized in the existing uppercase underscore style.
- The catch-all store directory is `FY2026_OTHER_CONTINUING_APPROPRIATIONS_EXTENDERS_HOMELAND_SECURITY_OTHER_MATTERS`.
- Every FY2026 store directory name is listed explicitly in Proposed Behavior; implementation should use that list verbatim.
- Every FY2026 source file, source division letter, short public-law label, and source division title is listed explicitly in Proposed Behavior; implementation should use that list verbatim unless file inspection proves a title/label typo.
- Keep the implementation style close to the 2024 setup instead of adding a broad corpus/year abstraction.
- `settings.subcommittee_stores` should remain the canonical division-to-store mapping unless implementation proves that impossible.
- Use the existing `data/bills/2026` filenames.
- Do not add broad extra source metadata for normal divisions; use only what the current source path needs.
- For catch-all sources, display original source division context and indicate the chunk is grouped under `CRX`.
- CRX source display should use short public-law labels like `P.L. 119-37` and `P.L. 119-75`, not full public-law titles.
- Preserve current extraction behavior if tests show it works for FY2026 body headers.
- Treat any configured source part producing fewer than 2 chunks as an ingestion failure.
- Do not add expected-keyword validation now; leave it as a possible future hardening idea.
- If routing returns no valid FY2026 division, return exactly `This question is incompatible with the FY2026 appropriations text available in LawSearch.` instead of querying every division.
- Treat old 2024 division names as invalid because the product is FY2026-only.
- Do not change saved conversation history behavior; the user will delete old DB data later.
- Do not change storage manager behavior; the user will delete old DB data/artifacts later.
- Tests should cover only FY2026 behavior.
- The user will run ingestion and provide errors/logs.
- Make small logical commits during implementation.

## Discoveries
- The current ingestion path infers both bill path and division letter from the Chroma store name, which is not sufficient for FY2026.
- The current route allowed-list and `divisions_filter` validation are tied to 2024 division names.
- The FY2026 consolidated source file has no Division C in the user-approved routable map.
- Homeland Security does not have a dedicated FY2026 annual appropriations division in this corpus; relevant continuation/extender material should route to `CRX`.
- `SourceDocument.metadata` already carries raw metadata to the frontend, but visible source cards/popovers currently show acronym, chunk id, summary/snapshot, and source snippet only.
- The three FY2026 source files expected by this plan are already present under `data/bills/2026/`.
- The FY2026 body headers are compatible with the existing `DIVISION X--` extraction pattern, including body headers that contain stripped `<<NOTE: ...>>` markup.
- The P.L. 119-37 table-of-contents text contains a typo in `CONTINUING APPROPRIATONS ACT, 2026`, but the body header extraction still locates Division A correctly and no configured source-title behavior was changed.

## Remaining Work
- Implementation work is complete.
- User-owned post-ingestion smoke validation remains as listed in the Validation section: ingest and activate a FY2026 vector store, then verify Agriculture/FDA, DOD, and DHS/FEMA/cybersecurity continuation/extender routing plus persisted `chunk_id`s and CRX original-division display.

## Diversions From Plan
- None.
