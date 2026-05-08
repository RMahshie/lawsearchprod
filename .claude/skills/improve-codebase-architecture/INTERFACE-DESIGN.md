# Interface Design

Use this when the user wants alternative interfaces for a chosen deepening candidate.

## Process

### 1. Frame The Problem Space

Before proposing interfaces, summarize:

- Constraints any new interface must satisfy.
- Dependencies and their categories from `DEEPENING.md`.
- What behavior should sit behind the seam.
- Current callers and tests.
- Compatibility risks.

Use an illustrative code sketch only to ground constraints, not as the final proposal.

### 2. Explore Alternatives

If the user explicitly asks for subagents or parallel design, spawn 3+ agents with independent briefs and different constraints:

- Minimize the interface: aim for 1-3 entry points.
- Maximize flexibility: support extension points and varied callers.
- Optimize the common caller: make the default case trivial.
- Use ports and adapters when cross-seam dependencies require them.

If subagents were not explicitly requested, generate the alternatives locally.

Each alternative should include:

1. Interface: types, methods, parameters, invariants, ordering, and error modes.
2. Usage example.
3. What implementation details sit behind the seam.
4. Dependency strategy and adapters.
5. Trade-offs: leverage, locality, and thin spots.

### 3. Compare And Recommend

Compare alternatives by depth, locality, seam placement, test surface, and LawSearch compatibility. Give a clear recommendation, including any hybrid design if useful.
