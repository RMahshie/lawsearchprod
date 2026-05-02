# Deterministic chunk ids that survive rebuilds

Each Chunk's `chunk_id` follows a stable shape — Division Acronym, an index, and a content-derived hash — rather than a random UUID assigned at ingest. The same Chunk produced by two ingestion runs gets the same id.

## Why

The Saved Question persistence model (see ADR-0001) stores citation pointers, not source text. Pointers are only useful if they keep resolving across rebuilds; random UUIDs would invalidate every Saved Question the moment we re-ingest. Deterministic ids let us rebuild stores freely (improved chunking, new embedding model, fresh Public Law) while keeping older Saved Questions citable.

## Trade-off accepted

Deterministic ids constrain the chunker — content shifts between runs (e.g. a chunk-size change) will produce different hashes and orphan old citations. We accept that: most rebuilds add or replace whole bills rather than re-chunk the same text, and Rehydrate is already designed to skip missing Chunks gracefully. The alternative — random ids plus a snapshot of source text in the saved-question DB — was rejected to avoid duplicating Chroma's job.
