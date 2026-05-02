# Thinking Speed is a per-stage strategy, not a single-knob mode

Thinking Speed (`quick` / `normal` / `long`) selects a *strategy* — a different OpenAI model for each pipeline stage (map, summary, reduce, synthesize, routing) — rather than swapping one model across the whole pipeline. The mapping lives in `MODEL_STRATEGIES` in `app/services/llm_factory.py`.

## Why

Stages have different cost-vs-quality curves. Map runs once per Chunk and dominates token spend, so it benefits from a cheaper model. Synthesize runs once per query and produces the user-visible answer with Number Annotations, so it benefits from a stronger model. Tying both to a single mode would force every Thinking Speed level to over- or under-invest in one of them. The current split was tuned by hand against real queries to find the combinations that make Source-backed Figures resolve reliably without burning budget on Map.

## Trade-off accepted

The strategy table is opinionated and hand-tuned, so adding a new stage or a new mode requires editing the table. A simpler "one model per request" knob would be self-explanatory but would either bloat cost on `quick` or starve quality on `long`.
