---
name: lawsearch-rag-debugging
description: Debug and tune the LawSearch RAG pipeline. Use when investigating ingestion, Chroma retrieval, embedding model mismatches, LangGraph map/reduce latency, thinking speed behavior, or frontend citation/source display.
---

# LawSearch RAG Debugging

## Use This For

- Query returns no answer, weak answer, too few chunks, or wrong sources.
- Ingestion/re-ingestion fails or Chroma has embedding dimension errors.
- Thinking speed/model behavior is confusing or slow.
- Citation UI, source chunks, or figure hover behavior looks wrong.

## Core Checks

1. Check ingestion before blaming RAG quality.
   - DHS should extract body text containing FEMA and Disaster Relief Fund.
   - If a division has only 1 chunk, inspect division header regex/normalization.

2. Check Chroma state before querying.
   - Count documents per configured division.
   - Verify active embedder matches `db/chroma/.embedding_model`.
   - Dimension mismatch usually means stale Chroma data or wrong embedding model.

3. Use `DEBUG=true` logs for latency.
   - Look for `RAG_DEBUG route`, `retrieve`, `map`, `reduce`, `synthesize`, `synthesize_skip`.
   - Do not log raw prompts, raw chunks, or full answers unless explicitly requested.

4. Interpret stages correctly.
   - `map`: per retrieved chunk, extracts facts and creates chunk summary.
   - `reduce`: per division, combines mapped chunk facts.
   - `synthesize`: only needed to combine 2+ division answers.

5. Keep semantics straight.
   - `max_results` is UI-controlled chunks per division.
   - Thinking speed controls model/answer behavior, not retrieval count.
   - Single-division queries should skip synthesis.

## Core Stage Logs

Use `DEBUG=true` when diagnosing retrieval, generation, number provenance, or history hydration issues. Keep pasted logs focused; most query bugs can be diagnosed from stage summaries and annotation gap logs without full chunk dumps.

Useful high-level lines:

- `RAG_DEBUG query_start`: request settings, model strategy, active vector store, embedding model.
- `RAG_DEBUG route`: selected divisions, `answer_mode`, flags, and short classifier reason.
- `RAG_DEBUG rewrite`: division-specific retrieval rewrites.
- `VECTOR_DEBUG retrieve`: Chroma collection, embedding model, requested and returned chunk counts.
- `RAG_DEBUG map`: per-chunk map latency and output sizes.
- `RAG_DEBUG reduce_start` / `reduce_done`: per-division reduce timing.
- `RAG_DEBUG synthesize_start` / `synthesize_done` / `synthesize_skip`: final synthesis behavior.
- `RAG_DEBUG query_done`: total query timing and stage counts.

Usually omit `VECTOR_DEBUG retrieved_doc` blocks unless the suspected issue is retrieval quality, missing chunks, duplicate chunks, wrong vector store, or wrong embedding model.

## Number Provenance Logs

These are the most useful logs for figure hover issues:

- `map_annotation_gaps`: a source-backed figure was extracted but not marked in map output.
- `reduce_annotation_input_gaps`: unmarked source figures reached reduce.
- `reduce_annotations_output`: reduce proposed or accepted derived annotations, or emitted unmarked figures.
- `synthesize_annotations_output`: final synthesis proposed or accepted derived annotations, or emitted unmarked figures.
- `derived_validation`: derived annotation acceptance/rejection details.
- `response_annotations`: annotations that actually reached the API response.

The path of failure matters:

- Gap appears at `map_annotation_gaps`: fix source extraction or marker insertion.
- Gap first appears at `reduce_annotations_output`: reduce restated a source figure without its marker, or created a derived marker that failed validation.
- Gap first appears at `synthesize_annotations_output`: synthesis restated a marked figure without preserving the marker, or proposed an invalid derived annotation.
- `response_annotations` has returned annotations but UI is not blue: inspect frontend marker parsing and markdown formatting.

## Derived Validation

Derived annotations are accepted only after deterministic backend checks. Important rejection reasons:

- `missing_marker`: proposed derived id was not present as `[[num:id]]` in the answer text.
- `missing_or_unparseable_displayed_marker_figure`: the backend could not find a parseable displayed dollar figure directly before the marker.
- `no_source_backed_inputs`: inputs did not flatten to source annotations.
- `displayed_proposed_value_mismatch`: displayed figure value did not match the proposed numeric value.
- `input_sum_mismatch`: displayed figure value did not match the sum of source-backed inputs.
- `duplicate_id`: proposed id was already used.

`rejected_details` includes the proposal id, model-proposed figure text, value, and input ids. This is enough to debug most derived-hover failures without pasting the whole answer.

## Source Marker Gaps

Source markers are inserted into mapped facts by exact figure text matching. The backend normalizes dollar parsing, but marker insertion still depends on the displayed source candidate being present in the mapped facts and retrieved source chunk.

Common causes:

- trailing punctuation being treated as part of the figure
- the model formatting a candidate differently from the chunk text
- repeated equal dollar figures with different labels
- a marker appearing after markdown closers such as `**`

The marker insertion code reuses a source annotation when the same source-backed figure appears multiple times. When multiple source annotations have the same figure but different labels, it uses distinct annotations first, then reuses the last one for repeats.

## History Hydration

Saved history stores source references and annotation snapshots. It does not store source text.

Useful history log:

- `HISTORY_DEBUG load`: saved source rows, hydrated sources, missing chunks, and first hydrated chunk ids.

If saved conversations lose source popovers:

- verify `hydrated_sources` is nonzero
- verify `missing_chunks` is zero or explainable
- verify the saved query has `number_annotations`
- verify the active vector store root and embedding model match the saved vector store

Do not add silent fallbacks for missing vector store state or invented chunk ids. Missing required state should fail loudly or skip the affected source, because fake fallbacks can make live queries look correct while history hydration breaks.

## Repeated Query Inconsistency

When identical questions return different numeric answers, compare saved runs before changing prompts or code:

- Restrict comparisons to the same normalized question and same `vector_store_id` / embedding model first.
- Compare selected divisions, saved source chunk ids and ranks, division answers, final answer, and `number_annotations`.
- Treat differing saved source chunk ids or ranks as the first observable retrieval divergence unless full stage logs prove an earlier rewrite difference.
- If divisions and sources are the same but visible figures differ, inspect map/reduce outputs or annotation logs; saved history does not persist exact mapped facts.
- Distinguish accepted derived annotations from answer markers that have no saved annotation object. A visible `[[num:drv_*]]` marker without a matching saved `number_annotations` entry will not behave like an accepted derived hover.
- If the needed `query_start`, `rewrite`, retrieved scores, or map outputs are no longer in logs, mark those stages as not directly observable instead of inferring certainty from saved answers.

## Minimal Log Paste Checklist

For number hover bugs, paste only:

- `query_start`
- `route`
- relevant `retrieve` summaries
- any `map_annotation_gaps`
- any `reduce_annotation_input_gaps`
- `derived_validation`
- `reduce_annotations_output`
- `synthesize_annotations_output`
- `response_annotations`

For retrieval bugs, also paste the top few `VECTOR_DEBUG retrieved_doc` lines with chunk ids and previews.

## Useful Verification

Run focused backend checks:

```bash
python3 -m pytest tests/test_ingestion_service.py tests/test_rag_service_units.py tests/test_query_models.py
```

Run frontend checks after UI changes:

```bash
npm run lint:frontend && npm run build:frontend
```

## Frontend Source Behavior

- Do not make division source chips hoverable in the answer card.
- Highlight literal dollar figures only when they match retrieved source snippets.
- Figure popovers should show all matching chunks with summaries.
- Leave Debug Chunks behavior untouched unless explicitly asked.
