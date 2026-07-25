# Three measurement planes

The Inspector produces evidence that lives on three different planes.
Conflating them — even informally — costs information about which
layer is actually under pressure.

| Plane | Question it answers | Indicator | Where recorded |
|---|---|---|---|
| **Inspector** | Is the Inspector's own contract (Rule, Finding, KernelAPI, Report) still sufficient? | CSI | `CSI.md` |
| **Knowledge Kernel model** | Does the data model express the phenomena the Inspector wants to measure? | EP | `CSI.md` (events), `NOTES.md` (criteria) |
| **Dataset** | What is the current health of the stored knowledge? | Findings (raw counts) | Per-run JSON reports, not `CSI.md` |

## What this file is for

It exists so that anyone recording an observation in the project
first asks: *which plane does this fact live on?* A finding about
the dataset should not become a contract concern; a renamed rule
should not become a dataset concern.

## References

- `CSI.md` — line-level log of CSI and EP events.
- `NOTES.md` — protocol for opening PIs from EP events.
- `CONTRACT.md` — Inspector contract v0.1 (frozen until evidence
  demands revision).
