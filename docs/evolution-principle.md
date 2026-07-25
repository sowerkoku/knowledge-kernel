# Evolution principle

The Knowledge Kernel follows a single evolution rule, distilled
from this session's work:

> The architecture does not evolve when new ideas appear; it
> evolves when recurring questions can no longer be answered
> correctly with the existing architecture.

A practical corollary of that rule — the question that should
dominate when considering ANY new component, rule, or
mechanism — is:

> *"Is there accumulated evidence justifying this addition, or
> is the addition anticipated because it would feel natural?"*

Evidence-led projects eventually shift their default question
from *"what's missing?"* to *"what is the evidence that
justifies this?"*. That shift is the mark of a mature design:
the burden of proof moves from the existing architecture having
to justify its limits to the proposal having to justify its
existence.

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

### Three classes of assets

Active assets in this repo fall into three categories, and
they are not equivalent:

| Class | Examples | Demonstrates value by |
|---|---|---|
| **Code** | `runs_diff.py`, rules, wrappers | Executing correctly. |
| **Constraints** | tests, contract tests, boundary tests, contracts | **Forbidding** entire classes of errors. |
| **Criterios** | `evolution-principle.md`, governance rules, the inverted question | **Changing decisions made before any code is written.** |

The third class is the least visible and the only one whose
principal effect is the *absence* of future code. That absence
is not a void: it is "justified non-software" — a decision
taken under an explicit criterion, which is a result in its
own right. Trying to convert this into a formal KPI is a
category mistake: the better the method works, the less data
there is to measure it directly. This is a common property of
preventive mechanisms — their success appears as an absence
of incidents, not as an abundance of events.

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

## Longitudinal audit

Technical architecture is reviewable in an afternoon; the
**evolution architecture** is not. A reviewer arriving in
six months will have to inspect commits, rejected proposals,
contract changes and their surrounding evidence — the
architecture of evolution only becomes visible across history.

The useful question for such a reviewer is therefore:

> *"Are the decisions taken during this period still
> coherent with the process the project itself declares?"*

That question is more demanding than any static review of
the current architecture. If the answer is *yes*, the
project has succeeded: many observations are recorded,
promotions are rare, contract changes are rarer still, and
each change carries a reconstructible chain of evidence
backward through the previous runs. That pattern — many
records, few promotions, very few contract changes,
reconstructible chains — is the empirical signature of a
working evolution architecture. It can only be confirmed
through extended use.