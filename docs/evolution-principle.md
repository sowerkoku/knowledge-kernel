# Evolution principle

The Knowledge Kernel follows a single evolution rule, distilled
from this session's work:

> The architecture does not evolve when new ideas appear; it
> evolves when recurring questions can no longer be answered
> correctly with the existing architecture.

This shifts the focus from creativity to *explanatory capacity*.
The system is judged by how well it answers the questions that
arise, not by how many abstractions it contains.

## Three actions, distinct and non-bypassable

Evidence handling in this repo decomposes into three actions:

| Action | Main artifact(s) | Result |
|---|---|---|
| **Registrar** | `docs/audits/`, `consumers/inspector/NOTES.md`, JSON run files | Evidence persisted |
| **Comparar** | `consumers/inspector/tools/runs_diff.py` and analogous future tools | Differences observed |
| **Documentar la promoción** | `CSI.md`, `EP-*`, PI entries, contract changes | Auditable record |

**Promotion itself is the architectural decision** —
opening a PI, modifying a contract, introducing a new model
concept, etc. The artefacts listed above are the **audit trail**
of that decision, not the decision itself.

This separation has a structural consequence: there is **no
direct path from Register to Promote**. Any promotion must pass
through:

    Observation
        │
        ▼
    Register
        │
        ▼
    Compare
        │
        ▼
    Hypothesis (if recurrence appears)
        │
        ▼
    Architectural decision
        │
        ▼
    Document the decision (CSI / EP / PI)

The friction is deliberate. Architecture is forced to answer,
in order:

1. Has this been recorded?
2. Has it been compared against prior evidence?
3. Is there recurrence?
4. *Only then* — does it merit an architectural decision?

This does not make the system evolve slower; it makes it evolve
**by evidence**, which is different.

## Discriminating change types

If this discipline is kept over time, it becomes relatively
straightforward to tell apart:

- **Operational noise** — single audit anomalies that do not
  recur.
- **Dataset changes** — content evolving, contract unaffected.
- **Model limits** — recurring phenomena the Kernel model
  cannot express (the EP signal).
- **Real evolution needs** — contract changes that follow
  accumulated evidence, not intuition.

That distinction, more than any single component, will determine
the project's stability over time.

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