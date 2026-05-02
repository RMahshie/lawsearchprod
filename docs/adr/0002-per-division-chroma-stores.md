# Per-Division Chroma stores

Each Division has its own Chroma store under the Vector Store Root, addressed by a Division-specific subdirectory. Retrieval queries one store per selected Division in parallel, never the union.

## Why

A single bill-wide store retrieved bloated, scattered results when a question touched multiple agencies, and sequential retrieval was slow. Splitting per Division lets the Route stage narrow scope deliberately and lets the Retrieve stage fan out across Divisions in parallel. A single store with a `division` metadata filter would have been simpler to ingest, but per-Division stores gave better isolation and faster retrieval in practice.

## Trade-off accepted

We pay rebuild cost when adding/changing Divisions and we manage 12 store directories instead of one. In exchange we get parallel retrieval, narrow scopes per query, and an acronym-based chunk-id namespace that survives rebuilds.
