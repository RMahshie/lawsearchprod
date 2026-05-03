# DeepSeek Structured Invocation

## Goal
Make DeepSeek model profiles work with the existing Query Pipeline by introducing a provider-aware structured invocation layer.

The new layer should preserve one LangGraph graph and one set of stage functions while routing structured-output calls through the correct provider strategy:

- OpenAI models continue to use LangChain structured output.
- All DeepSeek models use JSON mode plus Pydantic validation.

This should fix the observed DeepSeek failure:

```text
deepseek-reasoner does not support this tool_choice
During task with name 'classify_answer_mode'
```

## Non-Goals
- Do not create a separate DeepSeek LangGraph graph.
- Do not change the Query Pipeline topology.
- Do not change prompts beyond adding schema/JSON formatting instructions needed for DeepSeek JSON mode.
- Do not change the user-facing Thinking Speed names.
- Do not change retrieval, Chroma, ingestion, source hydration, persistence, or frontend rendering.
- Do not silently invent routing/classification fallbacks when schema validation fails.

## Current Behavior
The Query Pipeline has six structured LLM stages:

- `classify_answer_mode`: returns `AnswerModeDecision`.
- `route_divisions`: returns `RouteDecision`.
- `rewrite_division_queries`: returns `DivisionQueryPlan`.
- `map_chunk`: returns `MappedFacts`.
- `reduce_division`: returns `MarkedAnswer`.
- `synthesize_final`: returns `MarkedAnswer`.

Current call patterns:

- `classify_answer_mode`, `route_divisions`, and `rewrite_division_queries` directly call `.with_structured_output(...)` and then `invoke_with_retry(...)`.
- `map_chunk`, `reduce_division`, and `synthesize_final` call `invoke_structured_or_text(...)`.
- `invoke_structured_or_text(...)` first calls `llm.with_structured_output(schema)`. If structured invocation fails, it logs `structured_fallback` and falls back to plain text.

The DeepSeek profile currently constructs `ChatDeepSeek` with:

- `extra_body={"thinking": {"type": "enabled"}}` when `reasoning_effort` is set.
- `reasoning_effort="high"` or `reasoning_effort="max"` for thinking modes.

DeepSeek thinking mode is effectively the `deepseek-reasoner` path. LangChain structured output currently sends a forced tool/function choice. DeepSeek rejects that combination with:

```text
deepseek-reasoner does not support this tool_choice
```

## Proposed Behavior
Add a single provider-aware structured invocation API in `app/services/rag/llm_invocation.py`.

Target helper:

```python
def invoke_structured(
    llm: Any,
    payload: str | list[Any],
    *,
    schema: type[StructuredResponseT],
    model_spec: ModelSpec,
    stage: str,
    query_id: str,
    debug_log: Callable[..., None],
    fallback: Callable[[str], StructuredResponseT] | None = None,
) -> StructuredResponseT:
    ...
```

Behavior:

- If `model_spec.provider == "openai"`:
  - Use `llm.with_structured_output(schema)` and existing retry behavior.

- If `model_spec.provider == "deepseek"`:
  - Do not call `llm.with_structured_output(...)`.
  - Invoke JSON mode instead.
  - Add explicit schema instructions to the prompt/messages.
  - Parse the model content as JSON.
  - Validate with `schema.model_validate(...)`.
  - Retry once for retryable provider errors using existing `invoke_with_retry(...)`.
  - Fail loudly on invalid JSON or schema validation when `fallback is None`.
  - If `fallback` is supplied for map/reduce/synthesize, log the structured failure and use the existing text fallback path.

JSON-mode prompt behavior:

- For string prompts, append a compact instruction block:

```text
Return only valid JSON matching this schema. Do not wrap it in markdown.
Schema:
<schema_json>
```

- For chat message lists, append an extra human/user message with the same instruction block rather than mutating existing system prompts.
- Use the schema generated from Pydantic via `schema.model_json_schema()`.
- Keep the instruction generic and schema-derived; do not write stage-specific prompt content unless tests prove it is necessary.

Stage migration:

- `classify_answer_mode` should call `invoke_structured(...)` with `fallback=None`.
- `route_divisions` should call `invoke_structured(...)` with `fallback=None`.
- `rewrite_division_queries` should call `invoke_structured(...)` with `fallback=None`, while preserving its outer catch that falls back to original division queries if rewrite fails.
- `map_chunk` should call `invoke_structured(...)` with its current `MappedFacts(...)` fallback.
- `reduce_division` should call `invoke_structured(...)` with its current `MarkedAnswer(answer=text)` fallback.
- `synthesize_final` should call `invoke_structured(...)` with its current `MarkedAnswer(answer=text)` fallback.

Failure policy:

- Classification and routing failures should fail loudly. Do not silently guess answer mode or divisions.
- Rewrite may keep its existing fallback to original question because that fallback preserves the retrieval contract.
- Map/reduce/synthesize may keep their existing text fallback because the current code already treats that as compatibility behavior. The debug log must make this visible.
- Do not mask DeepSeek structured failures as successful derived annotations; if JSON mode cannot produce valid `MarkedAnswer`, derived annotations should be absent via the explicit text fallback path.

## Relevant Files
- `app/services/rag/llm_invocation.py`
- `app/services/rag/stages/classify.py`
- `app/services/rag/stages/route.py`
- `app/services/rag/stages/rewrite.py`
- `app/services/rag/stages/map_chunk.py`
- `app/services/rag/stages/reduce.py`
- `app/services/rag/stages/synthesize.py`
- `app/services/llm_factory.py`
- `app/services/rag/schemas.py`
- `tests/test_rag_service_units.py`
- `.agents/plans/deepseek-model-toggle.md`
- `.agents/plans/deepseek-structured-invocation.md`

## Assumptions
- The existing `ModelSpec.provider` and `ModelSpec.reasoning_effort` are sufficient to choose the structured invocation strategy.
- DeepSeek thinking mode supports JSON Output, but not the forced `tool_choice` emitted by LangChain structured output.
- `ChatDeepSeek` can be bound with JSON response format, likely through `llm.bind(response_format={"type": "json_object"})` or an equivalent LangChain/OpenAI-compatible parameter.
- If `ChatDeepSeek` does not accept JSON response format through `bind(...)`, the implementation should use the smallest wrapper-specific alternative and record it in Discoveries.
- DeepSeek structured output must always use JSON mode. Do not use LangChain's `.with_structured_output(...)` for DeepSeek, even when thinking is off.
- Existing schemas are acceptable for JSON-mode validation with Pydantic; no schema-shape migration is planned.

## Open Questions
None.

## Execution Steps
- [x] Resolve Open Questions before implementation.
- [x] Add `invoke_structured(...)` to `app/services/rag/llm_invocation.py`.
- [x] Add internal helpers for provider detection, schema-instruction rendering, payload augmentation, response content extraction, JSON parsing, and Pydantic validation.
- [x] Keep `invoke_structured_or_text(...)` as a compatibility wrapper around `invoke_structured(...)`.
- [x] Update `classify_answer_mode` to call `invoke_structured(...)` with `model_spec=classification_model`.
- [x] Update `route_divisions` to call `invoke_structured(...)` with `model_spec=routing_model`.
- [x] Update `rewrite_division_queries` to call `invoke_structured(...)` with `model_spec=rewrite_model`.
- [x] Update `map_chunk` to call `invoke_structured(...)` with `model_spec=map_model` and its current text fallback.
- [x] Update `reduce_division` to call `invoke_structured(...)` with `model_spec=reduce_model` and its current text fallback.
- [x] Update `synthesize_final` to call `invoke_structured(...)` with `model_spec=synthesize_model` and its current text fallback.
- [x] Add unit tests for OpenAI structured invocation still using `.with_structured_output(...)`.
- [x] Add unit tests for DeepSeek structured invocation using JSON mode and Pydantic validation without calling `.with_structured_output(...)`, for both thinking-off and thinking-on model specs.
- [x] Add unit tests for invalid DeepSeek JSON failure on classify/route with no fallback.
- [x] Add unit tests for DeepSeek JSON failure falling back to text for map/reduce/synthesize when a fallback is supplied.
- [x] Add or update stage tests proving classify/route/rewrite no longer directly call `.with_structured_output(...)` outside the helper.
- [x] Update this plan's Progress, Decisions, Discoveries, and Remaining Work as implementation proceeds.

## Validation
- `python3 -m pytest tests/test_rag_service_units.py tests/test_query_models.py tests/test_config.py`
- `npm run build:frontend`

Optional live validation, requiring installed dependencies, `DEEPSEEK_API_KEY`, `LAWSEARCH_MODEL_PROFILE=deepseek`, and a populated active vector store:

- Run one simple query in quick mode to verify DeepSeek non-thinking classify/route/rewrite behavior.
- Run one normal mode query to verify DeepSeek thinking classify/route/rewrite JSON-mode behavior.
- Run one long mode query that reaches reduce/synthesize to verify high/max thinking structured JSON behavior and annotation logs.
- Inspect `RAG_DEBUG classify`, `route`, `rewrite`, `map`, `reduce_annotations_output`, `synthesize_annotations_output`, and `response_annotations`.

## Documentation
- Update `.agents/plans/deepseek-model-toggle.md` to reference this plan as the structured-output compatibility follow-up.
- Update `docs/SETUP.md` only if the final DeepSeek setup requires an additional env variable or mode beyond `LAWSEARCH_MODEL_PROFILE` and `DEEPSEEK_API_KEY`.
- No frontend documentation expected.

## Progress
- 2026-05-03: Plan created after inspecting `.agents/PLANS.md`, current structured-output call sites, `llm_invocation.py`, and schema definitions. No implementation changes made.
- 2026-05-03: Updated plan per user direction: all DeepSeek structured calls must use JSON mode; do not use LangChain structured output for non-thinking DeepSeek either. No implementation changes made.
- 2026-05-03: Implemented provider-aware `invoke_structured(...)`, DeepSeek JSON-mode schema instructions, Pydantic validation, and stage migrations for classify, route, rewrite, map, reduce, and synthesize.
- 2026-05-03: Validation passed with `python3 -m pytest tests/test_rag_service_units.py tests/test_query_models.py tests/test_config.py`.
- 2026-05-03: Validation passed with `npm run build:frontend`; existing Vite font-resolution and chunk-size warnings remain.

## Decisions
- Keep one LangGraph graph; provider-specific behavior belongs in structured invocation, not graph topology.
- Centralize provider branching in `llm_invocation.py` so stage code stays focused on pipeline semantics.
- Use one DeepSeek structured-output path for all DeepSeek modes: JSON mode plus Pydantic validation.
- Classification and routing should fail loudly on structured-output failure unless the user explicitly approves a safe fallback policy.
- Use the full Pydantic JSON schema in DeepSeek JSON instructions for the first implementation so real output can be inspected before optimizing prompt size.
- Do not add a repair loop for invalid classify/route JSON in the first implementation; fail loudly and inspect the output.

## Discoveries
- `classify_answer_mode`, `route_divisions`, and `rewrite_division_queries` still call `.with_structured_output(...)` directly.
- `map_chunk`, `reduce_division`, and `synthesize_final` already use `invoke_structured_or_text(...)`, but that helper still starts with `.with_structured_output(...)`.
- The observed DeepSeek error happens before retrieval, during `classify_answer_mode`, because DeepSeek thinking mode rejects LangChain's forced `tool_choice`.
- The schemas are already centralized in `app/services/rag/schemas.py`, so JSON-mode validation can reuse existing Pydantic models.
- Local test execution can inherit `LAWSEARCH_MODEL_PROFILE` from `.env`; tests now force the OpenAI profile by default and opt into DeepSeek explicitly.

## Remaining Work
- Install the updated code in the Docker/runtime environment.
- Run the optional live DeepSeek validation with `LAWSEARCH_MODEL_PROFILE=deepseek`, `DEEPSEEK_API_KEY`, and a populated active vector store.
- Inspect real DeepSeek JSON outputs for classify, route, map, reduce, and synthesize before deciding whether to add a repair retry or shorten schema instructions.
