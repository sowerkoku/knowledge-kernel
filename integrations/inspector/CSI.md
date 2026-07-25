# Contract Stability Index & Expressivity Pressure — Tracking

Two distinct observations, kept apart:

  - **CSI** traces how much the Inspector contract (Rule, Finding,
    KernelAPI, Report) has had to change to support new rules.

  - **EP** traces how often a rule had to be reframed because the
    underlying Knowledge Kernel model did not express the
    phenomenon the rule was meant to inspect. A rule that gets
    renamed or reduces its scope due to a model limitation is an
    *expressivity pressure*, not a *contract change*.

These are two different kinds of evidence:

  - CSI measures the Inspector's own stability.
  - EP measures the Kernel model's representational reach.

Conflating them (e.g. reporting a renamed rule as a contract
change) loses information about which layer the limit actually
appears in.

## Entries

| Commit | Rules | Contract changes | CSI | EP events | Notes |
|---|---|---|---|---|---|
| 779387c | 5 (stale_entity, low_confidence_entity, missing_runs_on, cycles_invalid, no_declared_relations) | 0 | 5 : 0 | 1 | Phase 2 start (global analysis); no_declared_relations validates policy filters |
| 545ab6b | 4 | 0 | 4 : 0 | 1 | cycles_invalid confirms cmdb_impact is sufficient for graph traversal |
| 8978530 | 3 | 0 | 3 : 0 | 1 | missing_runs_on validates consumer-side filtering |
| 2d3d7ba | 2 | 0 | 2 : 0 | **1** | low_confidence_dependency renamed to low_confidence_entity: Kernel confidence is per-entity, not per-relation |
| 335a925 | 1 | 0 | 1 : 0 | 0 | Evolution policy + CSI tracking added |
| 7935cae | 1 | 0 | 1 : 0 | 0 | v0.1 frozen; 5 pillars codified |

## Definitions

    CSI = (number of rules implemented) / (number of contract changes to date)
    EP  = (number of rules that reframed scope due to Kernel model limits)

EP is counted when a rule was *intended* at a different scope and
the implementation could not proceed without renaming or reducing
remit. Pure policy changes are not EP events; only cases where the
Kernel model itself lacked the expression.

EP may grow without CSI dropping. A high EP alongside an unchanged
contract is informational: it points at the *Kernel* model, not the
Inspector.

## Decision rules

- Adding a rule without contract change → CSI numerator up.
- Renaming or reducing scope of a rule because the Kernel model
  cannot represent the rule's intended scope → EP numerator up.
- First contract change → CSI becomes finite; same evidence
  expectations as `CONTRACT.md`.
- If EP rises sharply relative to rule count, that is signal to
  revisit the **Kernel** model (PI-N territory), not the Inspector.

## Historical EP events

| Rule (intended) | Tried for | Reframed as | Kernel limitation observed |
|---|---|---|---|
| low_confidence_dependency | inspect per-relation confidence | low_confidence_entity | public API exposes `confidence_level` per entity, not per relation |

