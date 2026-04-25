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
