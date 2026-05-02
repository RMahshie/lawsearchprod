# Number Annotations come from structured LLM output, not regex post-processing

Every visible dollar figure in an answer is bound to a Number Annotation produced by the LLM via `with_structured_output(...)`, not extracted from the answer text by regex matching after the fact. Source-backed Figures must name the originating Chunk; Derived Figures must name an equation and inputs.

## Why

Regex over the answer markdown would happily match any dollar figure, but it cannot tell whether two identical figures (`$2,847,000,000` appearing twice) refer to the same line item or to two different programs that happen to share a value, and it cannot enforce that a number actually came from somewhere. Forcing the LLM to emit the annotation at the same time as the figure makes the model commit to a Chunk citation or a calculation; the annotation is the proof, not a guess made after the fact.

## Trade-off accepted

Higher prompt complexity, larger structured-output schemas, and a strict validator (`validate_kind_payload`) that rejects malformed annotations. Worth it: this is what makes the citation hover UI trustworthy rather than decorative.
