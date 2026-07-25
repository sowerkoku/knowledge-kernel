# Evolution principle

The Knowledge Kernel follows a single evolution rule, distilled
from this session's work:

> The architecture does not evolve when new ideas appear; it
> evolves when recurring questions can no longer be answered
> correctly with the existing architecture.

This shifts the focus from creativity to *explanatory capacity*.
The system is judged by how well it answers the questions that
arise, not by how many abstractions it contains.

## Three rates of change

The system naturally separates into three temporal scopes. Each
scope changes at its own pace, and each has a distinct observability
instrument:

| Rate | Examples | Observation tool |
|---|---|---|
| **Slow**   | KernelAPI, Rule/Finding protocol, layers, boundaries | CSI |
| **Medium** | Rules, EP events, platforms.py, scaffolding | EP-*, `platforms.py` |
| **Fast**   | Runs, findings, policies, datasets | `runs_diff` |

The instruments do not compete: CSI watches whether the slow layer
is still sufficient; EP watches whether the medium layer is being
pushed by recurring limits; `runs_diff` watches the fast layer.
A failure at one rate does not imply failure at another.

**Friction as a signal.** If a layer starts absorbing changes that
belong to a different rate, friction appears — too rigid where it
should be flexible, too volatile where it should be stable. That
friction is itself evidence about the architecture and a candidate
input to the next evolution cycle.

## Burden of proof

> The burden of proof rests on the change, not on the existing
> architecture.

While the current model continues to explain new evidence
satisfactorily, the correct decision is to leave it alone. The
absence of changes is itself a valid result. Stability here is not
a preference; it is what the evidence supports.

Practical corollaries:

- A new rule that fits v0.1 → add it; CSI numerator rises.
- An EP that does not recur → close it; do not open a PI.
- A question whose answer the current system produces, even
  awkwardly → answer it; postpone the abstraction.
- A question that the current system **cannot** answer correctly
  → there is now evidence for evolution. But not before.

This rule protects against two opposite mistakes at once:
over-construction (adding abstractions in anticipation) and
paralysis (refusing abstractions even when evidence demands them).
Stability becomes a property the system can have, not a stance its
maintainers must hold.