---
description: Internal architecture — L2 engine, indexes, atomic reload, thread safety.
audience: maintainers
layer: internal
---

# Architecture — knowledge-kernel

**Audience:** kernel maintainers and contributors. This document describes
the internals. For "how to use" see `~/.hermes/skills/knowledge-kernel/SKILL.md`.

## L2 In-Memory Index Engine

The L2 engine eliminates N+1 latency by materializing deterministic indexes
on first load.

### Pattern

1. **Cold path** — load YAML once, parse, validate, build indexes (one-time cost)
2. **Warm path** — every query resolves against in-memory indexes (sub-ms)
3. **Rebuildable** — indexes are derived; the YAML files remain the canonical
   factual store

### Constraints honored

- YAML = canonical factual store
- Memory = deterministic derived indexes (rebuildable)
- API = stable contract (no breaking changes from L2)
- Telemetry = observes usage
- Discovery = proposes changes
- Humans = curate facts
- Agents = reason on top

### Non-goals (intentionally out of scope)

- No proposal queues
- No evidence engines
- No distributed caches
- No mutation APIs
- No complex evidence levels
  (DECLARED → DISCOVERED → VERIFIED → CORROBORATED)

## Atomic Reload Semantics

Reloads follow the "build-in-temporaries, swap atomically" pattern:

```python
# CORRECT: build in temporaries → validate → atomic swap
new_indexes = build_indexes(<path>)
validate(new_indexes)
swap(new_indexes)
```

Readers see complete state or nothing — never partial state. The distinction
between **cache** and **derived views** is documented separately.

## Thread Safety

The L2 engine is read-only after initialization. All mutating operations
(rebuild, atomic swap) acquire a write lock; reads are lock-free against a
sealed controller.

## Engine Generation

Every reload increments `engine_generation`. Telemetry requests always
carry the generation that produced their view. See
`docs/observability.md` for the telemetry contract.
