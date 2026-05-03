# DeepSeek Model Toggle

## Goal
Introduce a configurable model-provider strategy layer so LawSearch can run the existing Query Pipeline with either the current OpenAI GPT 5.4 strategy or a DeepSeek comparison strategy.

The DeepSeek comparison strategy should use the exact stage/speed table in Proposed Behavior. Keep model selection easy to toggle so side-by-side comparisons can be run without editing code each time.

Also update the OpenAI/ChatGPT profile so normal and long Thinking Speeds use medium-level thinking for the non-full-`gpt-5.4` model slots.

Make `classify`, `route`, and `rewrite` independently configurable in both model profiles instead of sharing one fixed `routing` model slot.

## Non-Goals
- Do not change prompts, routing rules, answer formatting, Number Annotation semantics, source hydration, ingestion, Chroma behavior, or frontend UI behavior.
- Do not change Thinking Speed names exposed by the API or frontend (`quick`, `normal`, `long`).
- Do not remove the existing OpenAI model strategy.
- Do not make DeepSeek the only supported provider.
- Do not add real-query benchmark results in this change; the change only enables comparison.

## Current Behavior
`app/services/llm_factory.py` owns all chat model selection.

Current routing model:

- `routing`: `gpt-5.4-mini`

Current strategies:

| Thinking Speed | Stage | Current Model |
| --- | --- | --- |
| `quick` | `map` | `gpt-5.4-nano` |
| `quick` | `summary` | `gpt-5.4-nano` |
| `quick` | `reduce` | `gpt-5.4-mini` |
| `quick` | `synthesize` | `gpt-5.4-mini` |
| `normal` | `map` | `gpt-5.4-mini` |
| `normal` | `summary` | `gpt-5.4-nano` |
| `normal` | `reduce` | `gpt-5.4` with `reasoning_effort="low"` |
| `normal` | `synthesize` | `gpt-5.4` with `reasoning_effort="medium"` |
| `long` | `map` | `gpt-5.4-mini` |
| `long` | `summary` | `gpt-5.4-nano` |
| `long` | `reduce` | `gpt-5.4` with `reasoning_effort="medium"` |
| `long` | `synthesize` | `gpt-5.4` with `reasoning_effort="medium"` |

`resolve_model(thinking_speed, task)` returns a `ModelSpec`.

Current classification/routing/rewrite coupling:

- `classify_answer_mode(...)` calls `resolve_model(state["thinking_speed"], "routing")`.
- `route_divisions(...)` calls `resolve_model(state["thinking_speed"], "routing")`.
- `rewrite_division_queries(...)` calls `resolve_model("quick", "routing")`, so rewrite is always pinned to the quick routing model and ignores the request Thinking Speed.
- `llm_factory.py` has a single global `ROUTING_MODEL`, not per-speed `classify`, `route`, or `rewrite` entries.

`describe_model_strategy(thinking_speed)` returns the response/log label used in `model_used`.

`create_chat_model(model, task, reasoning_effort)` always instantiates `ChatOpenAI`.

Pipeline stages call `create_chat_model(...)` and then use either plain text invocation or LangChain structured output:

- `classify`, `route`, and `rewrite` call `.with_structured_output(...)` directly.
- `map`, `reduce`, and `synthesize` call `invoke_structured_or_text(...)`, which attempts structured output and falls back to plain text when structured invocation fails.

## Proposed Behavior
Add an explicit model strategy selector controlled by environment configuration.

Env variable:

- `LAWSEARCH_MODEL_PROFILE=openai` uses the current GPT 5.4 strategy.
- `LAWSEARCH_MODEL_PROFILE=deepseek` uses the DeepSeek comparison strategy.

If unset, default to `openai` so existing local and deployed behavior does not change.

Add provider-aware model specifications that can represent:

- provider: `openai` or `deepseek`
- model name
- temperature
- thinking mode for DeepSeek: `disabled` or `enabled`
- DeepSeek reasoning effort when thinking is enabled: `high` or `max`
- OpenAI reasoning effort when applicable

Use LangChain provider classes directly:

- `ChatOpenAI` for OpenAI specs.
- `ChatDeepSeek` from `langchain-deepseek` for DeepSeek specs.

Install dependency:

- Add `langchain-deepseek` to `requirements.txt`.

Add required env for DeepSeek:

- `DEEPSEEK_API_KEY` is required only when `LAWSEARCH_MODEL_PROFILE=deepseek`.
- Optional `DEEPSEEK_API_BASE` may be supported by `ChatDeepSeek`; if used, document it only if the implementation confirms the installed wrapper reads it.

For easy comparisons:

- Keep `LAWSEARCH_MODEL_PROFILE` as the only required toggle between whole-strategy comparisons.
- Include the provider/model/thinking settings in `format_model_spec(...)` and `describe_model_strategy(...)` so logs, progress events, and saved `model_used` make the active strategy obvious.
- Keep the strategy table centralized in `llm_factory.py`; do not scatter per-stage provider logic across stage files.
- Split the old shared `routing` model slot into explicit `classify`, `route`, and `rewrite` slots for every Thinking Speed in every profile.
- Make `rewrite_division_queries(...)` pass the request Thinking Speed into `resolve_model(...)` instead of hard-coding quick routing.
- Add tests that switch the env/configured profile and assert exact resolved models for every stage/speed.

DeepSeek strategy table:

| Stage | Quick model | Quick effort | Normal model | Normal effort | Extended model | Extended effort |
| --- | --- | --- | --- | --- | --- | --- |
| `classify` | `deepseek-v4-flash` | off | `deepseek-v4-flash` | high | `deepseek-v4-flash` | high |
| `route` | `deepseek-v4-flash` | off | `deepseek-v4-flash` | high | `deepseek-v4-flash` | high |
| `rewrite` | `deepseek-v4-flash` | off | `deepseek-v4-flash` | high | `deepseek-v4-flash` | high |
| `retrieve` | ChromaDB | none | ChromaDB | none | ChromaDB | none |
| `map` extract facts | `deepseek-v4-flash` | high | `deepseek-v4-flash` | high | `deepseek-v4-flash` | high |
| `summary` / `snapshot` | `deepseek-v4-flash` | off | `deepseek-v4-flash` | high | `deepseek-v4-flash` | high |
| `reduce` | `deepseek-v4-pro` | high | `deepseek-v4-pro` | high | `deepseek-v4-pro` | max |
| `synthesize` | `deepseek-v4-pro` | high | `gpt-5.4` | medium | `deepseek-v4-pro` | max |

Use these internal names when mapping the user-facing table:

- Quick means existing `quick`.
- Normal means existing `normal`.
- Extended means existing `long`.
- DeepSeek effort `off` means thinking disabled.
- DeepSeek effort `high` or `max` means thinking enabled with that effort.
- The `retrieve` row is not an LLM slot and remains ChromaDB-only.

OpenAI/ChatGPT profile update:

- Keep the profile name `openai`.
- Add configurable `classify`, `route`, and `rewrite` slots to the OpenAI strategy table for `quick`, `normal`, and `long`.
- Keep OpenAI quick `classify`, `route`, and `rewrite` unchanged at `gpt-5.4-mini`.
- Set OpenAI normal `classify`, `route`, and `rewrite` to `gpt-5.4-mini(reasoning=medium)`.
- Set OpenAI long `classify`, `route`, and `rewrite` to `gpt-5.4-mini(reasoning=medium)`.
- Leave `quick` unchanged.
- Set `normal` `map` to `gpt-5.4-mini(reasoning=medium)`.
- Set `normal` `summary` to `gpt-5.4-nano(reasoning=medium)`.
- Set `long` `map` to `gpt-5.4-mini(reasoning=medium)`.
- Set `long` `summary` to `gpt-5.4-nano(reasoning=medium)`.
- Preserve the existing `normal` synthesize, `long` reduce, and `long` synthesize `gpt-5.4(reasoning=medium)` slots unless the user specifies otherwise.

## Relevant Files
- `app/services/llm_factory.py`
- `app/core/config.py`
- `requirements.txt`
- `tests/test_rag_service_units.py`
- `.env.example`
- `README.md`
- `docs/SETUP.md`
- `docs/RAILWAY_DEPLOYMENT.md`
- `docker-compose.yml`
- `app/services/rag/stages/classify.py`
- `app/services/rag/stages/route.py`
- `app/services/rag/stages/rewrite.py`
- `app/services/rag/stages/map_chunk.py`
- `app/services/rag/stages/reduce.py`
- `app/services/rag/stages/synthesize.py`

The stage files should not need provider-specific model-mapping logic. `rewrite_division_queries(...)` will need a targeted call-site update so it resolves the `rewrite` slot using the request Thinking Speed rather than hard-coding quick routing.

## Assumptions
- DeepSeek V4 models should be addressed by explicit model names `deepseek-v4-flash` and `deepseek-v4-pro`, not legacy aliases.
- `ChatDeepSeek.with_structured_output(...)` supports the structured-output path needed by the existing Pydantic schemas.
- DeepSeek thinking mode can be passed through LangChain either through constructor kwargs or model kwargs without touching stage code.
- The comparison toggle is process-wide through `LAWSEARCH_MODEL_PROFILE`; do not add request-level or UI-level model profile overrides.
- Existing saved question storage can keep using the `model_used` string without schema changes.
- OpenAI embeddings remain unchanged. This plan affects chat models only.
- Splitting `routing` into `classify`, `route`, and `rewrite` is a model-selection refactor only; it should not change prompt contents or stage outputs by itself.

## Open Questions
None.

## Execution Steps
- [x] Resolve the remaining Open Questions about logging detail and missing-key failure timing.
- [x] Add `langchain-deepseek` to `requirements.txt`.
- [x] Extend settings in `app/core/config.py` with `LAWSEARCH_MODEL_PROFILE` and optional DeepSeek key/base configuration, preserving the default OpenAI behavior.
- [x] Refactor `ModelSpec` in `app/services/llm_factory.py` to include provider and provider-specific thinking parameters while keeping stage call sites simple.
- [x] Define named strategy tables for `openai` and `deepseek`.
- [x] Replace the single global `ROUTING_MODEL` with per-profile, per-speed `classify`, `route`, and `rewrite` entries.
- [x] Update the OpenAI profile with the confirmed medium-thinking changes for normal and long non-full-`gpt-5.4` slots while leaving quick unchanged.
- [x] Update `resolve_model(...)` and `describe_model_strategy(...)` to read the active profile and produce exact labels for comparison.
- [x] Update `classify_answer_mode(...)` to resolve the `classify` task instead of the shared `routing` task.
- [x] Update `route_divisions(...)` to resolve the `route` task instead of the shared `routing` task.
- [x] Update `rewrite_division_queries(...)` to resolve the `rewrite` task using `state.get("thinking_speed", "normal")` instead of `resolve_model("quick", "routing")`.
- [x] Update `create_chat_model(...)` to instantiate `ChatOpenAI` or `ChatDeepSeek` based on model/provider selection.
- [x] Ensure DeepSeek structured output uses the `ChatDeepSeek` default structured-output path unless implementation testing shows a different method is required.
- [x] Keep `temperature=0` for non-thinking deterministic routes where the provider supports it.
- [x] Update unit tests around `resolve_model(...)`, `describe_model_strategy(...)`, and model-profile settings for both profiles.
- [x] Add tests that assert the DeepSeek profile exact classify, route, rewrite, map, summary, reduce, and synthesize mappings for quick, normal, and long.
- [x] Add tests that assert the OpenAI profile exact classify, route, rewrite, map, summary, reduce, and synthesize mappings for quick, normal, and long.
- [x] Add a test proving rewrite is speed-aware by asserting normal or long rewrite resolves to the corresponding profile entry, not the quick entry.
- [x] Add wrapper-level coverage proving stage call sites still use `.with_structured_output(...)` through existing stage tests and a focused rewrite test.
- [x] Update env/docs examples to mention `LAWSEARCH_MODEL_PROFILE=deepseek` and `DEEPSEEK_API_KEY`.
- [x] Update this plan's Progress, Decisions, Discoveries, and Remaining Work during implementation.

## Validation
- `python3 -m pytest tests/test_rag_service_units.py`
- `python3 -m pytest tests/test_query_models.py`
- `npm run build:frontend`

Optional real-provider checks after implementation, requiring `DEEPSEEK_API_KEY`:

- Run one direct `ChatDeepSeek.with_structured_output(RouteDecision)` invocation.
- Run one direct `ChatDeepSeek.with_structured_output(MappedFacts)` invocation.
- Run one direct `ChatDeepSeek.with_structured_output(MarkedAnswer)` invocation.
- Run one live LawSearch query with `LAWSEARCH_MODEL_PROFILE=deepseek`, `DEBUG=true`, and a populated active vector store; inspect `query_start`, `route`, `map`, `reduce`, `synthesize`, and `response_annotations` logs.

## Documentation
- `.env.example`: add `LAWSEARCH_MODEL_PROFILE` and `DEEPSEEK_API_KEY`.
- `README.md`: add a short model-profile toggle note only if README currently documents runtime env.
- `docs/SETUP.md`: add DeepSeek setup only if setup docs currently list env variables.
- `docs/RAILWAY_DEPLOYMENT.md`: add deploy env notes only if production may use the DeepSeek profile.
- Do not update frontend docs unless the toggle becomes user-facing.

## Progress
- 2026-05-02: Plan created after inspecting `.agents/PLANS.md`, current `llm_factory.py`, and model-strategy call sites. No implementation changes made.
- 2026-05-02: Updated plan with user-provided DeepSeek table and env-only toggle decision. Added OpenAI/ChatGPT profile update request as a remaining explicit mapping question. No implementation changes made.
- 2026-05-02: Confirmed OpenAI/ChatGPT profile mapping: quick unchanged; normal and long non-full-`gpt-5.4` slots get medium reasoning. No implementation changes made.
- 2026-05-02: Inspected classify/route/rewrite model resolution. Added plan work to split the shared `routing` slot into per-speed `classify`, `route`, and `rewrite` slots for both profiles, and to make rewrite speed-aware. No implementation changes made.
- 2026-05-03: Implemented provider-aware model profiles, DeepSeek and OpenAI strategy tables, env/config wiring, speed-aware classify/route/rewrite resolution, docs/env updates, and focused tests.
- 2026-05-03: Validation passed with `python3 -m pytest tests/test_rag_service_units.py tests/test_query_models.py tests/test_config.py`.
- 2026-05-03: Validation passed with `npm run build:frontend`; existing Vite font-resolution and chunk-size warnings remain.

## Decisions
- Keep the default profile as `openai` so the current behavior remains unchanged until explicitly toggled.
- Use an explicit model profile toggle rather than overwriting the existing GPT 5.4 table.
- Make the model profile toggle environment-only through `LAWSEARCH_MODEL_PROFILE`; do not add request-level or frontend controls.
- Keep the comparison toggle centralized in `llm_factory.py`; stage files should remain provider-agnostic.
- Use explicit DeepSeek V4 model names rather than legacy aliases.
- Implement the DeepSeek profile from the exact user-provided table in Proposed Behavior.
- In the OpenAI profile, leave quick-speed model choices unchanged and add medium reasoning to normal/long `gpt-5.4-mini` and `gpt-5.4-nano` slots.
- Make `classify`, `route`, and `rewrite` independently configurable model tasks in each profile.
- Preserve current OpenAI quick classify/route/rewrite behavior while allowing normal and long classify/route/rewrite to use medium-reasoning ChatGPT slots.
- Include the active profile and full provider/thinking labels in `model_used` and progress/debug model labels so comparison runs are easy to identify.
- Let missing `DEEPSEEK_API_KEY` fail when a DeepSeek chat model is first instantiated, not at application startup. This keeps the default OpenAI profile and config inspection usable without a DeepSeek key.

## Discoveries
- Current model selection is centralized in `app/services/llm_factory.py`.
- `routing` is a separate model slot used by classify, route, and rewrite paths.
- `summary` is a distinct model slot from `map`, even though both run during per-Chunk mapping.
- `describe_model_strategy(...)` currently reports only `map`, `reduce`, and `synthesize`, not `summary` or `routing`.
- Existing tests assert exact current model mappings in `tests/test_rag_service_units.py`.
- `rewrite_division_queries(...)` currently ignores request Thinking Speed by calling `resolve_model("quick", "routing")`; this must change for route/rewrite comparison toggles to behave as requested.

## Remaining Work
- Install the updated Python dependency set in any environment that will run `LAWSEARCH_MODEL_PROFILE=deepseek`.
- Optional real-provider DeepSeek structured-output and live-query smoke checks remain, requiring `DEEPSEEK_API_KEY` and a populated active vector store.
