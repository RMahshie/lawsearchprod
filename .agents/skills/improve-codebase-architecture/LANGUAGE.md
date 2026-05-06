# Architecture Language

Shared vocabulary for architecture suggestions.

## Terms

**Module**
Anything with an interface and an implementation. Scale-agnostic: function, class, package, or tier-spanning slice.
Avoid: unit, component, service.

**Interface**
Everything a caller must know to use the module correctly: type signature, invariants, ordering constraints, error modes, required configuration, and performance characteristics.
Avoid using "signature" when the wider interface is meant.

**Implementation**
Code inside a module. Distinct from **adapter**: an adapter describes the role a concrete implementation plays at a seam.

**Depth**
Leverage at the interface. A module is **deep** when a lot of behavior sits behind a small interface. A module is **shallow** when the interface is nearly as complex as the implementation.

**Seam**
A place where behavior can be altered without editing in place. The location where a module's interface lives.
Avoid: boundary.

**Adapter**
A concrete thing satisfying an interface at a seam. Describes role, not substance.

**Leverage**
What callers get from depth: more capability per fact they need to learn.

**Locality**
What maintainers get from depth: change, bugs, knowledge, and verification concentrated in one place.

## Principles

- Depth is a property of the interface, not the implementation.
- A deep module can have internal seams used by its own tests; those do not need to become external interface.
- The deletion test: if deleting a module removes complexity, it was pass-through. If complexity reappears across callers, it was earning its keep.
- The interface is the test surface.
- One adapter means a hypothetical seam. Two adapters means a real seam.

## Rejected Framings

- Depth as implementation-lines divided by interface-lines.
- Interface as only a TypeScript `interface` or method signature.
- Boundary as a substitute for seam.
