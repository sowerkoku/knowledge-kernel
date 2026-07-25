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
