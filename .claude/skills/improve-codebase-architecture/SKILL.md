---
name: improve-codebase-architecture
description: Use when the user asks to review or improve LawSearch architecture, find refactoring opportunities, deepen shallow modules, reduce coupling, improve testability, or make the codebase easier for agents to navigate. Produces architecture candidates first and does not implement without an approved plan.
---

# Improve Codebase Architecture

Surface deepening opportunities: refactors that turn shallow modules into deeper modules with more leverage at the interface and better locality for maintenance.

This skill is adapted for LawSearch from Matt Pocock's `improve-codebase-architecture` skill. Follow this repo's execution-plan workflow and Codex subagent rules.

## Required Context

Before proposing candidates, read:

- `CONTEXT.md` for LawSearch domain language.
- `docs/adr/` for decisions that should not be re-litigated casually.
- `AGENTS.md` and `.agents/PLANS.md` for repo workflow.
- The files directly involved in the area under review.

Use LawSearch domain terms from `CONTEXT.md`. In product/design discussion, prefer **Saved Question** over "conversation" unless referring to existing code/API names.

## Architecture Vocabulary

Use these terms consistently. See `LANGUAGE.md` for fuller definitions.

- **Module**: anything with an interface and an implementation.
- **Interface**: everything a caller must know to use a module correctly, including invariants, ordering, errors, configuration, and performance.
- **Implementation**: code inside a module.
- **Depth**: leverage at the interface. A deep module hides a lot of behavior behind a small interface.
- **Seam**: where an interface lives; a place behavior can be altered without editing in place.
- **Adapter**: concrete implementation satisfying an interface at a seam.
- **Leverage**: what callers get from depth.
- **Locality**: what maintainers get from depth: change, bugs, knowledge, and verification concentrated in one place.

Core checks:

- **Deletion test**: if deleting the module makes complexity vanish, it was pass-through. If complexity reappears across callers, it was earning its keep.
- The interface is the test surface.
- One adapter means a hypothetical seam. Two adapters means a real seam.

## Process

### 1. Explore

Inspect the current implementation first. Look for friction:

- Understanding one LawSearch concept requires bouncing through many small modules.
- A module is shallow: its interface is nearly as complex as its implementation.
- Tests need to reach past the interface to verify behavior.
- Required runtime state is passed implicitly, duplicated, or silently defaulted.
- Tightly coupled modules leak facts across seams.
- Existing ADRs and actual code drift apart.

Use subagents only if the user explicitly asks for subagents, parallel exploration, or delegation. Otherwise explore locally.

### 2. Present Candidates

Return a numbered list of candidates. For each:

- **Files**: files/modules involved.
- **Problem**: architecture friction, grounded in code.
- **Solution**: plain-English shape of the deeper module or better seam.
- **Benefits**: how leverage, locality, and tests improve.
- **ADR/context impact**: note any ADR conflict or `CONTEXT.md` vocabulary gap.

Do not propose detailed interfaces yet. Ask which candidate the user wants to explore.

### 3. Grill The Chosen Candidate

Once the user chooses, ask focused questions until the design is explicit:

- What behavior sits behind the seam?
- What callers must know, and what should be hidden?
- Which dependencies are in-process, local-substitutable, remote-owned, or true external? See `DEEPENING.md`.
- What tests should survive internal refactors?
- What failure modes must be loud?
- Which LawSearch terms need sharpening in `CONTEXT.md`?

If the user rejects a candidate for a durable reason, offer to record an ADR only when future architecture reviews would otherwise re-suggest it.

### 4. Plan Before Implementation

For implementation work, create an Execution Plan under `.agents/plans/` and wait for approval unless the user explicitly says to proceed.

The plan should name:

- Current interface and implementation.
- Proposed interface.
- Migration steps.
- Tests to replace or add.
- Compatibility concerns for Saved Questions, Chunks, Number Annotations, vector store roots, and prompt/routing behavior when relevant.

## Optional References

- `LANGUAGE.md`: detailed architecture vocabulary.
- `DEEPENING.md`: dependency categories and testing strategy.
- `INTERFACE-DESIGN.md`: use only when the user wants alternative interface designs; subagents remain opt-in.
