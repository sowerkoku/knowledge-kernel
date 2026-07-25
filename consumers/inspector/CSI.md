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

| Commit | Rules | Contract changes | CSI | EP | Notes |
|---|---|---|---|---|---|
| 48b1928 | 5 | 0 | 5 : 0 | 0 | docs: anchor evolution-principle.md + log principle codification in CSI (pure documentation, no rule/contract change) |
| e4c9403 | 5 | 0 | 5 : 0 | 0 | docs: codify the three-action chain (Register / Compare / Document promotion) — architecture docs only, no rule or contract change |
| 779387c | 5 (stale_entity, low_confidence_entity, missing_runs_on, cycles_invalid, no_declared_relations) | 0 | 5 : 0 | 0 | Phase 2 start (global analysis); no_declared_relations validates policy filters |
| 545ab6b | 4 | 0 | 4 : 0 | 0 | cycles_invalid confirms cmdb_impact is sufficient for graph traversal |
| 8978530 | 3 | 0 | 3 : 0 | 0 | missing_runs_on validates consumer-side filtering |
| 2d3d7ba | 2 | 0 | 2 : 0 | **1 (EP-001)** | low_confidence_dependency renamed to low_confidence_entity: Kernel confidence is per-entity, not per-relation |
| 335a925 | 1 | 0 | 1 : 0 | 0 | Evolution policy + CSI tracking added |
| 7935cae | 1 | 0 | 1 : 0 | 0 | v0.1 frozen; 5 pillars codified |

(`EP` per commit counts the events introduced by that commit. EP-001
is the only one so far.)

## Definitions

    CSI = (number of rules implemented) / (number of contract changes to date)
    EP  = (number of rules that reframed scope due to Kernel model limits)

Each EP event is recorded individually below — the summary is a
counter, not a replacement.

## Decision rules

- Adding a rule without contract change → CSI numerator up.
- Renaming or reducing scope of a rule because the Kernel model
  cannot represent the rule's intended scope → EP numerator up.
- First contract change → CSI becomes finite; same evidence
  expectations as `CONTRACT.md`.
- Opening a PI is **not** triggered by a number. It is triggered by
  *recurrence of the same phenomenon*. See EP-001 below and
  `NOTES.md` for the protocol.

## Historical EP events

Each event is a typed, dated entry. The summary counter at the top
is for at-a-glance reference; full evidence lives below.

---

### EP-001

| Field | Value |
|---|---|
| ID | EP-001 |
| Title | Relation-level confidence not representable |
| Status | cerrado (closed — not waiting for more evidence; no recurrence has surfaced) |
| Type | EP-R (renamed) + EP-N (narrowed scope) |
| Date | 2026-07-24 |
| Inspector commit | 2d3d7ba |
| Rule — original | `low_confidence_dependency` |
| Rule — final | `low_confidence_entity` |
| Tried for | per-relation confidence inspection |
| Reframed to | per-entity confidence inspection |
| Reason | Public Kernel API exposes `confidence_level` per entity, not per relation. The intended phenomenon (confidence as a relation property) has no expression in the data model. |
| Contract change | No |
| Inspector change | No |
| PI opened | No (isolated event, no recurrence yet) |
| Reopen criteria | A second rule attempting per-relation evidence with the same limitation, in the same period. Add `EP-002` and escalate to hypothesis. |

