# Six-stage map-reduce query graph instead of a single RetrievalQA chain

The Query Pipeline is a hand-rolled LangGraph state graph with six explicit stages — Route, Rewrite, Retrieve, Map, Reduce, Synthesize — rather than a single `RetrievalQA` (or equivalent) chain over a bill-wide store.

## Why

The product's value proposition is auditable answers: every figure traceable to a Chunk, every claim attributable to a Division. A single chain hides intermediate state and offers no natural place to attach provenance. Splitting the work into named stages means each stage accumulates explicit, inspectable state — Mapped Facts per Chunk, a Division-level answer per Division, then a final cross-Division synthesis with Number Annotations stamped on top. Logs, streaming progress events, and saved-question records all hang off the same stage boundaries.

## Trade-off accepted

More code, more LLM calls per query (two per Chunk in Map alone), and the operational overhead of fan-out/reduce reducers. We pay this for full audit-trace observability and the ability to evolve any stage independently — the alternative was opaque single-chain answers that would not support Source-backed Figures.
