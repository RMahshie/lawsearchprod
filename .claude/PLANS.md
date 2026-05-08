# Execution Plans

Execution Plans are task-specific markdown files for complex, ambiguous, risky, or multi-file work.

Create plans in:

.agents/plans/<task-name>.md

This file defines the plan format. It is not the active plan.

## Rules

Before implementation:
- Inspect relevant code first.
- Write the plan before editing implementation files.
- Include assumptions and open questions.
- Wait for user approval before coding unless the user explicitly says to proceed.

During implementation:
- Follow the plan step by step.
- Update Progress after meaningful changes.
- Record major Decisions and Discoveries.
- Keep Remaining Work accurate.
- Stop before making large unplanned scope changes.

After implementation:
- Run relevant tests, linting, type checks, or manual checks.
- Update docs if behavior, setup, APIs, or user-facing flows changed.
- Summarize files changed, validation run, and remaining risks.

## Required Structure

# <Task Name>

## Goal
What this change should accomplish.

## Non-Goals
What this change will not do.

## Current Behavior
How the system works now.

## Proposed Behavior
How the system should work after the change.

## Relevant Files
Files or directories likely involved.

## Assumptions
Things believed to be true before implementation.

## Open Questions
Questions needing user input or code investigation.

## Execution Steps
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Validation
Commands/checks that prove the work is correct.

## Documentation
Docs, comments, README/API/UI copy updates needed.

## Progress
Timestamped notes as work happens.

## Decisions
Important implementation choices and why.

## Discoveries
Unexpected findings from the codebase.

## Remaining Work
Current unfinished work.