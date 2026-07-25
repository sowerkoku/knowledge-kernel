# Contract Stability Index — Tracking

This is a living record, not a dashboard. Each entry corresponds to a
commit that touches `integrations/inspector/`.

## Entries

| Commit | Rules | Contract changes | CSI | Notes |
|---|---|---|---|---|
| 545ab6b | 4 (`stale_entity`, `low_confidence_entity`, `missing_runs_on`, `cycles_invalid`) | 0 | ∞ | 4 rules / 0 contract changes; graph traversal validated; cmdb_impact sufficient |
| 8978530 | 3 (`stale_entity`, `low_confidence_entity`, `missing_runs_on`) | 0 | ∞ | v0.1 contract held across 3 rules; CSI empirico estable |
| 2d3d7ba | 2 (`stale_entity`, `low_confidence_entity`) | 0 | ∞ | v0.1 contract held; rule added; 8 new tests green |
| 335a925 | 1 (`stale_entity`) | 0 | ∞ | Evolution policy + CSI tracking added |
| 7935cae | 1 (`stale_entity`) | 0 | ∞ | v0.1 frozen; 5 pillars codified |

## Definition

CSI = (number of rules implemented) / (number of contract changes to date)

When `contract_changes = 0`, CSI is reported as ∞. The metric is only
meaningful once at least one rule beyond the first has been
implemented cleanly. Track daily.

## Decision rule

- Adding a rule without contract change → CSI goes up.
- Modifying the contract → CSI drops to a finite number; the
  proposal MUST cite the rule that required the change.
