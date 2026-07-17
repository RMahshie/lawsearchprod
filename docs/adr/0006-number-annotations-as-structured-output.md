# Number Annotations come from structured LLM output, not regex post-processing

Every visible dollar figure in an answer is bound to a Number Annotation produced by the LLM via `with_structured_output(...)`, not extracted from the answer text by regex matching after the fact. Source-backed Figures must name the originating Chunk; Derived Figures must name an equation and inputs.

## Why

Regex over the answer markdown would happily match any dollar figure, but it cannot tell whether two identical figures (`$2,847,000,000` appearing twice) refer to the same line item or to two different programs that happen to share a value, and it cannot enforce that a number actually came from somewhere. Forcing the LLM to emit the annotation at the same time as the figure makes the model commit to a Chunk citation or a calculation; the annotation is the proof, not a guess made after the fact.

## Trade-off accepted

Higher prompt complexity, larger structured-output schemas, and a strict validator (`validate_kind_payload`) that rejects malformed annotations. Worth it: this is what makes the citation hover UI trustworthy rather than decorative.

## Stage-local Figure Handles

Reduce and Synthesize do not copy visible dollar figures and canonical `[[num:...]]` ids independently. Before each call, the backend replaces a bound figure-marker pair with a self-describing stage-local Figure Handle such as `{{F1:$25,000}}`. Keeping the display amount inside the atomic handle preserves the fact's local meaning without asking the model to join an opaque alias to a separate registry. The prompt does not duplicate a figure registry; backend state owns that mapping and the model copies only exact whole handles present in its evidence. The backend then renders the annotation's exact figure plus canonical marker.

Map's structured `source_numbers` sidecar improves labels but is not trusted as exhaustive. The backend deterministically completes it from every exact dollar-figure occurrence that appears in both the mapped fact and its originating Chunk. This is not a model retry or provenance inference across sources: the same Chunk remains the Source-backed Figure's single provenance boundary.

New calculations use a local `{{D1}}` handle plus a matching structured Derived Figure proposal. The backend resolves its input handles, validates source lineage and arithmetic, assigns the canonical Derived Figure id, and only then renders the figure and marker.

Raw dollar figures, unknown handles, detached markers, and invalid Derived Figure handles fail closed at the response boundary: the unverified figure is omitted without guessing a source. This is validation and rendering, not regex provenance inference. Each model stage is invoked at most once; malformed structured output or provider errors are surfaced rather than retried or sent through a second plain-text call.
