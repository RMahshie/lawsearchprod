# Saved Questions store citation pointers, not source text

When persisting a Saved Question, we store only the chunk id, rank, Chunk Snapshot, and Chunk Summary for each cited Chunk — never the source text itself. Source text is rehydrated from Chroma at view time using `(vector_store_root, division, chunk_id)`. Chunks that no longer exist in the recorded Vector Store Root are silently skipped, leaving the Saved Question viewable but thinner.

## Why

Source text would otherwise be duplicated in two places (Chroma + the saved-question DB) with no clear source of truth, and the duplicate would drift on rebuilds. Storing pointers keeps Chroma authoritative, makes saved entries small, and lets stylistic improvements to chunking (e.g. better summaries) flow through to old entries the next time they are viewed.

## Trade-off accepted

A Saved Question against a Vector Store Root that is later rebuilt or removed will lose some of its citations. We treat this as acceptable: the answer text and Number Annotations remain intact, only some hover/source rows go missing. Tolerating this is preferable to the alternative — freezing source text snapshots and managing a second persistence pathway for citation content.
