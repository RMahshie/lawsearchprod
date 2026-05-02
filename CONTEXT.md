# LawSearch

A RAG system over U.S. federal appropriations bills. Users ask questions in natural language and get answers with citations back to specific chunks of bill text.

## Language

**Division**:
A LawSearch retrieval bucket. The unit the router selects, retrieval queries, and the reduce stage summarizes. Usually wraps one Bill Division 1:1; CRX is the exception.
_Avoid_: subcommittee, section, bucket.

**Bill Division**:
Congress's own structural unit, literally headed "DIVISION X" inside a Public Law. Distinct from a LawSearch **Division** only when multiple Bill Divisions are aggregated under one Division (currently only CRX).

**CRX**:
The "Continuing Resolution Extras" Division. The one synthesized Division that aggregates Bill Divisions covering continuing appropriations, extenders, Homeland Security, and miscellaneous matter that doesn't belong to a single subcommittee. For FY2026 it wraps nine Bill Divisions across two Public Laws.

**Source Part**:
One `(public_law, division_letter, division_title, source_file)` tuple identifying a slice of bill text. A **Division** is composed of one or more Source Parts; only CRX has more than one.

**Division Acronym**:
Stable short marker for a Division (DOD, CRX, LHHS, etc.). Used in citations and embedded in chunk IDs, so it is load-bearing — not just a display label.

**Chunk**:
An immutable slice of bill text embedded into a Division's vector store, addressed by a stable `chunk_id`. The id format encodes the Division Acronym so chunks survive rebuilds and can be rehydrated from Chroma when serving citations.
_Avoid_: passage, snippet, document.

**Chunk Summary**:
A one-line LLM-generated sentence describing what a Chunk says. Used in the citation hover UI.

**Chunk Snapshot**:
A short LLM-generated label (a few words) naming what a Chunk is about. Used as the row title in source excerpt lists. Distinct from a Chunk Summary — snapshot is a title, summary is a sentence.

**Number Annotation**:
Structured provenance for a single visible dollar figure in an answer. Either a **Source-backed Figure** or a **Derived Figure**.

**Source-backed Figure**:
A Number Annotation traceable to a single Chunk — the figure appears verbatim (or near-verbatim) in bill text. Atomic; not computed.

**Derived Figure**:
A Number Annotation produced by combining other annotations (source-backed or derived) via a stated equation. Carries a short non-chain-of-thought rationale, never a reasoning trace.
_Avoid_: calculated figure, computed figure.

**Annotation Marker**:
The inline link inside answer markdown that ties a visible figure to its Number Annotation. A marker may live in the top-level answer or in a Division summary; the annotation records both placements as targets.

**Thinking Speed**:
User-selected pipeline strategy that controls per-stage model selection and retrieval parameters. Three modes: `quick`, `normal`, `long`. Not a single-knob temperature toggle — different graph stages (map, summary, reduce, synthesize) may use different OpenAI models within one mode.
_Avoid_: reasoning effort, depth, mode.

## Pipeline stages

The **Query Pipeline** is the LangGraph state graph that turns a question into an answer. Six named stages run in order:

**Route**:
Pick which Divisions to query for this question. Bypassed when the request supplies an explicit `divisions_filter`.

**Rewrite**:
For each selected Division, rewrite the user's question into a Division-tailored retrieval query. The query that hits Chroma for DOD differs from the query that hits Chroma for LHHS, even though the original user question was the same.

**Retrieve**:
For each selected Division, pull the top-`k` Chunks from that Division's vector store using its rewritten query.

**Map**:
For each retrieved Chunk, two LLM calls: extract structured facts (figures, agencies, programs) and produce a one-line Chunk Summary.

**Reduce**:
For each Division, fold its mapped Chunks into a single Division-level answer.

**Synthesize**:
Combine all Division answers into the final cross-Division answer, attaching Number Annotations (Source-backed and Derived) and emitting Annotation Markers.

## Persistence

**Saved Question**:
A persisted record of one question, its final answer, and the citation pointers (chunk ids, ranks, snapshots, summaries) needed to display sources later. Source text is **not** stored — it is fetched from Chroma on view via Rehydrate. The codebase calls this a "Conversation"; see Flagged ambiguities.
_Avoid_: conversation, chat.

**Vector Store Root**:
The versioned filesystem root containing a built set of Chroma stores (one subdirectory per Division). A Saved Question records the Vector Store Root it was built against; if that root is rebuilt or removed, some of its Chunks may fail to rehydrate.

**Rehydrate**:
Looking up a Chunk's source text and metadata in Chroma at view time using `(vector_store_root, division, chunk_id)`. Missing Chunks are silently skipped — a Saved Question stays viewable, just thinner.

## Routing

**Routing Alias**:
A free-text hint string maintained per Division that lists the agencies, programs, and keywords pulling that Division into the Route stage's selection. An editorial artifact — captures human knowledge about which Division covers which real-world topics.

## Relationships

- A **Division** is composed of one or more **Source Parts**
- A **Bill Division** belongs to exactly one Public Law
- Each non-CRX **Division** wraps exactly one **Bill Division**; **CRX** wraps many
- A **Chunk** belongs to exactly one **Division** and is stored in that Division's Chroma store under a **Vector Store Root**
- A **Number Annotation** is either Source-backed (points to one Chunk) or Derived (points to one or more other Annotations via an equation)
- An **Annotation Marker** in answer or Division-summary markdown resolves to exactly one Number Annotation
- A **Saved Question** stores citation pointers; source text is fetched via **Rehydrate** against the recorded **Vector Store Root**

## Example dialogue

> **User:** "How much does the bill spend on FEMA?"
> **System:** Route picks **CRX** (FEMA falls under Homeland Security, bundled into CRX). Rewrite tailors the question for CRX's content. Retrieve pulls the top-`k` **Chunks** from the CRX Chroma store. Map turns each Chunk into structured facts and a **Chunk Summary**. Reduce produces the CRX **Division** answer. Synthesize emits the final answer with **Annotation Markers**; FEMA's headline figure is a **Source-backed Figure** pointing to one CRX Chunk, while a "FEMA + related disaster relief" total may be a **Derived Figure** with an equation over two Source-backed Figures.
> **User (later, after a re-ingest):** "Open my saved question from last month."
> **System:** Loads the **Saved Question**. Citations are **Rehydrated** from the recorded **Vector Store Root**. One CRX Chunk no longer exists in the rebuilt store, so its source row is omitted; the answer text and Number Annotations remain intact.

## Flagged ambiguities

- The persistence API and DB schema use **"Conversation"** for what is actually a single Q&A, not a multi-turn dialogue. Resolved: the domain term is **Saved Question**; "Conversation" persists as a code/API name but should not be used in product or design discussion.
