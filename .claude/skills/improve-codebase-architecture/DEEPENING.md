# Deepening

How to deepen a cluster of shallow modules safely.

## Dependency Categories

### 1. In-Process

Pure computation, in-memory state, no I/O.

Deepening strategy: merge behavior behind a better interface and test through that interface directly. No adapter is needed.

### 2. Local-Substitutable

Dependencies with local test stand-ins, such as an in-memory filesystem, SQLite, PGLite, fake Chroma, or local test doubles.

Deepening strategy: keep the dependency behind an internal seam. Tests use the local substitute through the deepened module's public interface.

### 3. Remote But Owned

Owned services across a network seam.

Deepening strategy: define a port at the seam. The deep module owns the logic; transport is injected as an adapter. Tests use an in-memory adapter; production uses HTTP, gRPC, queue, or similar.

### 4. True External

Third-party systems such as OpenAI, LangSmith, hosted databases, or external APIs.

Deepening strategy: inject a port for the external dependency. Tests provide a mock adapter. Keep provider-specific behavior out of broad callers.

## Seam Discipline

- Do not introduce a seam unless at least two adapters are justified, usually production plus test.
- A deep module may have internal seams for implementation tests. Do not expose those internal seams through the external interface only for tests.
- Required runtime state should move through explicit interfaces. Avoid silent fallback when the substitute does not preserve the same contract.

## Testing Strategy

- Replace shallow-module tests once the deepened interface has stronger coverage.
- Write tests against observable outcomes through the interface.
- Tests should survive internal refactors.
- If tests must reach past the interface, the module shape is suspect.
