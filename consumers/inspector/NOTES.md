# Inspector — implementation notes (technical observations)

This file is **not** part of the Inspector contract. It records
observations made during rule implementation that are useful to the
next implementer but do not change v0.1.

## Expressivity Pressure (EP) — how to record

When a rule must be reframed because the Kernel model does not
express the intended phenomenon, record it both in **CSI.md**
(under "Historical EP events") and inline below with what was
attempted and what the model lacked.

EP is *informational*, not a verdict. A growing EP count alongside
an unchanged contract is signal about the **Kernel model**, not the
**Inspector contract**. These two developments have very different
prescriptions:

  - High EP → consider whether the Kernel's data model needs
    additional fields. That is PI-N territory, not v0.2-of-the-Inspector.
  - High CSI denominator with N contract changes → consider whether
    the Inspector contract needs revision. That is v0.2-of-the-Inspector.

Keep these separations.

## Recurrence protocol — when to open a PI

The decision to open a research programme from EP events is
*pattern-based*, **not** number-based. A fixed numeric threshold
(e.g. "EP ≥ 3") would be arbitrary. Recurrence of an underlying
phenomenon is the signal.

Sequence:

1. **EP isolated** → record the event with type (EP-R, EP-N,
   EP-C, EP-K...) and a short reason. Keep everything in CSI.md.
2. **Several EP of the same type** → formulate a hypothesis about
   the model's missing representation (analogous to a
   PI hypothesis). Document it; do **not** open a PI.
3. **Same hypothesis recurs across different rules** → at this
   point the phenomenon is no longer incidental. Open a PI.
4. **PI accumulates evidence** → decide whether the model needs
   an additional field/concept. Only then does the Kernel v0.x
   revision start.

A single EP event is not a PI. A second similar event is a
*signal*, also not a PI. The third event of the same shape is the
smallest piece of evidence that *might* justify a PI — and even
then, the PI is opened, not a model revision. Revisions follow
PI conclusions, not PI openings.

This mirrors the PI-01 protocol that already governs Agent
Workspace hypotheses.

## Confidence granularity (2026-07-24)

**Observation**: the public Knowledge Kernel API exposes confidence
for an **entity's evidence** (`cmdb_get(...).evidence.confidence_level`)
but not for **individual relations** (`entity.relations[].confidence`
does not exist).

**Consequence** for rule candidates:

- `low_confidence_dependency` (inspects per-relation confidence) is
  **not implementable** under v0.1. Renamed to
  `low_confidence_entity` — the rule inspects per-entity
  confidence only.
- Any future rule that wants per-relation evidence will need the
  Kernel API to grow that field. Until then, the rule is parked.

**Status of the parked candidates**:

| Candidate | Reason parked |
|---|---|
| `low_confidence_dependency` | Needs per-relation confidence |
| `cycles_invalid` | Needs graph traversal API surfaces; not yet attempted |
| `missing_runs_on` | Has analogous issue: must inspect relation absence per kind |

These are technical observations, **not** architectural proposals.
No PI is opened for them. If the Kernel grows the required public
API later, the candidates return to the backlog.

## Audit findings — integrations/hermes/tools/* (2026-07-25)

Single audit run, NOT enough to constitute EP. Listed here so
future audits can detect recurrence. The full report organised
by plane (Tool / Dataset / Performance) is at:

    docs/audits/2026-07-25-hermes-tools.md

### run_pilot.py — L3 iteration results

- Total: 16 questions across 4 categories.
- KAR (Kernel Adoption Rate) global: 100%.
- FGR (Fact Grounding Rate) global: 100%, but by-category:
  - infrastructure: 0% (4 questions, 0 facts)
  - dependencies: 0% (4 questions, 0 facts)
  - endpoints: 0% (4 questions, 0 facts)
  - agents: 100% (4 questions, 6 facts, 28 assertions)
- P95 latency: 815ms — target was 250ms; criterion NOT met.

### Dataset state observed

- 33 validation warnings at the YAML validation layer.
- Cold-start latency in `cmdb_get` (~815ms first call, ~0ms
  subsequent): suggests cache miss — not a contract issue.
- "no encontrado" answers for Ollama, MySQL, app-server-01 are
  accurate — those entities are genuinely absent from the
  dataset.

### Status

These are run-time findings, **not** EP events. No rule was
framed and limited by the Kernel model — the dataset genuinely
lacks the data. Tools themselves worked correctly against the
live dataset_hash=157d23fa.

To qualify for promotion, a recurrence of these patterns across
later audits would be needed.

---

## Architectural transition: KernelEngine becomes the canonical runtime representation

### Observation

During the L2 retrieval benchmark (dataset `157d23fa`, 53 entities,
2026‑07‑25), `cmdb_context` was observed to take ~800 ms per call
regardless of warm/cold/random/hot mode. Other public APIs
(`cmdb_exists`, `cmdb_get`, `cmdb_impact`, `cmdb_list`, `cmdb_assert`,
`cmdb_search`, `cmdb_validate`, `cmdb_engine_info`, `cmdb_stats`)
showed the expected O(1) over‑index pattern after first load
(P50 ≈ 0.2–0.5 ms; first call ≈ ≈ 900 ms due to engine reload).

Profiling traced the 800 ms to `cmdb.validator.load_entities_with_paths()`,
which `re`-parses every YAML in `entities_dir` on **every** call to
`cmdb_context`. None of the other public APIs follow that path;
they read through the `KernelEngine` exclusively.

### Diagnosis

This is not a performance symptom. Two representations of the
same dataset coexist in runtime:

```
              entities_dir/*.yaml
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
   KernelEngine                  load_entities_with_paths()
   (id‑indexed Entity tree)      (rebuilt dict on every call)
         │                           │
         │                           ▼
         │                       dict{id: raw_entity}  ← thrown
         ▼                       away once assertions.py exits scope
   9 of 10 public APIs
   read through here
```

The duplication violates a principle the project already adopted:
**Single Source of Truth**. The 800 ms latency is a consequence,
not the cause.

### Closing observation (architectural, not symptomatic)

The project has been moving toward treating `KernelEngine` as the
**canonical runtime representation** of knowledge. Nine of the ten
public APIs already do so. Where this transition was incomplete
shows through `cmdb_context`. Completing it is not optimising one
function; it is finishing an architectural move that the project
has already begun elsewhere.

Implications that follow once the transition is declared complete:

- No public API reconstructs entities.
- No public API parses YAML directly.
- Every query is served through `KernelEngine`.
- All derived information is born from `KernelEngine`.

These are architectural properties, not performance targets.

### Open technical task

**Restore Single Source of Truth in runtime:**
eliminate the parallel dataset representation used by `cmdb_context`,
so that all knowledge information flows from the canonical runtime
representation held by `KernelEngine`.

#### Invariancia a restaurar

> Durante la ejecución del proceso existe una única
> representación canónica del dataset. Ninguna API pública
> reconstruye una representación equivalente mediante un
> segundo parseo de los YAML.

#### Acceptance criteria

1. The runtime invariant holds: one canonical representation,
   held by `KernelEngine`.
2. All information consumed by `cmdb_context` is obtained from
   `KernelEngine` or from public APIs built exclusively on it.
3. The existing `cmdb_context` tests continue to pass.
4. A regression test asserts that `cmdb_context` returns the
   declared response keys for both known and unknown `agent_id`
   values.
5. A gating test verifies that no execution path reachable from
   `cmdb_context` reconstructs the dataset by parsing YAML files.

#### Out of scope (explicitly)

- Modifying the dataset format.
- Modifying the public contract (`cmdb/api.py` stays at v0.1).
- Introducing an additional caching mechanism (Redis, SQLite,
  in‑memory shadow layer, etc.) — these would relocate the
  duplication, not remove it.

#### Bookkeeping

- Not an EP — the problem is fully characterised and the
  solution is constrained by an existing principle. An EP is for
  phenomena whose resolution requires recurrence of evidence.
- Not an entry in `CSI.md` — `CSI.md` records changes that
  affect the public contract or the Inspector evolution policy.
  This task touches neither.
- The transition status above is annotated as the **closing
  observation of an architectural move already in progress**,
  not a new architectural decision.

### Status

- Characterisation: ✅ complete.
- Implementation: ⏳ not started; awaits an explicit activation
  decision (or remains in this notes file until something else
  activates it).

