# Number Provenance

LawSearch answers are markdown, but dollar figures can carry hidden provenance markers so the UI can show source-backed and calculation-backed popovers.

## Contract

The answer text is the source of truth for what the user sees. A marker immediately after a displayed dollar figure binds that visible figure to structured metadata:

```md
**FEMA total:** **$5,080,537,369** [[num:drv_dhs_1]]
```

The API returns matching metadata in `QueryResponse.number_annotations`. The frontend strips hidden markers before display and replaces the visible figure with a blue hover/click target.

There are two annotation kinds:

- `source`: an atomic dollar figure backed by a retrieved chunk.
- `derived`: a calculated dollar figure backed by other source or derived annotations and deterministic arithmetic validation.

## Source Annotations

Source annotations are created during the map stage. The map LLM extracts relevant facts and source-backed dollar figures from one retrieved chunk. The backend then inserts source markers into the mapped facts.

Source annotations store only provenance references:

- `id`
- `kind: "source"`
- `figure`
- `value`
- `label`
- `source.chunk_id`

They do not store source text, source quotes, chunk summaries, or snapshots. Source text comes from `QueryResponse.sources`, and saved history rehydrates source text from Chroma using `vector_store_id + chunk_id`.

## Derived Annotations

Derived annotations are proposed by reduce or synthesis when the model combines source-backed numbers.

The model returns:

- marked markdown answer text
- proposed derived annotation metadata

The backend treats proposed derived annotations as untrusted until validation passes.

Validation requires:

- the proposed id has a `[[num:id]]` marker in the answer text
- the displayed dollar figure directly before that marker is parseable
- every input id exists and flattens to source-backed annotations
- the displayed figure value matches the proposed numeric value
- the displayed figure value matches the sum of source-backed inputs within rounding tolerance

If validation fails, the derived annotation is omitted. The marker is stripped by the frontend, so the figure renders as plain markdown text.

## Displayed Figure vs Proposed Figure

For derived numbers, the displayed figure is read from the answer text next to the marker. This is intentional.

The structured LLM output field named `figure` is model-proposed metadata. Internally this is treated as `proposed_figure`, because the model may put a label there:

```json
{
  "id": "drv_dhs_1",
  "figure": "FEMA total",
  "value": 5080537369,
  "label": "FEMA total",
  "equation": "$1,483,990,000 + $99,528,000 + $3,497,019,369 = $5,080,537,369",
  "input_ids": [
    "src_operations",
    "src_procurement",
    "src_assistance"
  ]
}
```

The accepted `NumberAnnotation.figure` becomes the displayed figure from the answer text:

```md
**FEMA total:** **$5,080,537,369** [[num:drv_dhs_1]]
```

That means:

- answer text owns the UI target
- annotation metadata owns the label, equation, rationale, and input graph
- prompts should still ask for exact visible figures, but validation does not depend on the model following that perfectly

## Frontend Rendering

`frontend/src/components/QueryResults.tsx` renders annotations first.

The renderer:

1. Finds visible dollar figures followed by `[[num:id]]`.
2. Allows markdown closers such as `**` between the figure and marker.
3. Looks up `id` in `result.number_annotations`.
4. Checks whether the annotation targets the current answer scope.
5. Replaces the figure with a markdown link target.
6. Strips all remaining hidden markers.

Source popovers show the source chunk and highlighted source figure. Derived popovers show the total, readable equation, rationale, and expandable source-backed input rows.

## Persistence

Saved query history stores `number_annotations` as a JSON snapshot. It stores source row references and summaries/snapshots, but not source text. On load, source text is rehydrated from the active saved vector store by `vector_store_id + chunk_id`.

This preserves number hovers for saved conversations without recomputing answers or derivations.

## Failure Modes

If source-backed figures are not blue:

- inspect `map_annotation_gaps`
- the issue likely happened before reduce
- common causes are punctuation/format mismatches or a source candidate that did not appear exactly in both mapped facts and source chunk text

If derived figures are not blue:

- inspect `derived_validation`
- rejected annotations will include `rejected_details`
- common causes are missing marker, unparseable displayed marker figure, non-source-backed inputs, or arithmetic mismatch

If logs show annotations returned but the UI renders bold black numbers:

- inspect markdown around the marker
- the frontend linker must recognize patterns like `**$10** [[num:id]]`

