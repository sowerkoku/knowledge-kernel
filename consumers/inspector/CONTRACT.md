# Knowledge Inspector — Contract v0.1

**Status: frozen.** Changes to the types listed here are contract
changes. They follow the same care as changes to the Kernel's public
API: evidence first, then promotion, with backward-compatibility
considered.

## Scope

The Inspector is a consumer of the Knowledge Kernel. It produces
findings — falsifiable evidence about the state of the Kernel. It
**never**:

- Modifies the dataset.
- Modifies the Kernel.
- Decides whether something warrants a new component.
- Opens a research programme (PI-N).

## Types in this contract

```
Rule           Protocol. The unit of business logic.
Finding        Frozen dataclass. One falsable result.
KernelAPI      Thin façade exposing only cmdb.api.__all__.
RunContext     Pins (now, dataset_hash, generation, inspector_version,
                policy_version) that refrigerate determinism.
Policy         External to the contract. Anything a rule reads at
                evaluation time but that does not live in the rule's
                source file. Owned by the operator, not the rule.
Reporter       Serialises a RunContext + findings into a deterministic
                JSON document.
Evidence       Frozen dataclass. Raw facts consumed by Rules; reusable
                across them.
```

Adding a new public type, renumbering fields, or changing the shape
of `Finding.falsation` is a v0.2 decision. Promote it with evidence,
not anticipation.

## Invariants — the contract's five pillars

### Pillar 1 — Public-API only

Inspector modules **must not** import from `cmdb.*` directly. The
only sanctioned import is `inspector.kernel_api.KernelAPI`. The
Rule declaration `consumes_api: tuple[str, ...]` lists every public
function the rule relies on, and the Inspector runtime verifies
the declaration against `KernelAPI` before evaluating the rule.

**Why preserve**: if a rule ever needs internal Kernel access, that
is an evidence point. Channel it (PI-N, contract revision, or rule
rebuild) — do not bypass.

### Pillar 2 — Determinism

The Reporter pins the run with:
- `generated_at` (now)
- `inspector_version`
- `policy_version`
- `dataset_hash`, `generation`
- `parameters` (the policy used)

Two runs with identical pins MUST produce byte-equal reports. Any
divergence is attributable to a change in the dataset, the policy,
or the Inspector itself — and that is detectable.

### Pillar 3 — Contract vs Policy separation

- **Kernel** = contract (facts): `evidence.observed_at`,
  `confidence_level`, `relation.target`. The Kernel owns these.
- **Inspector Policy** = operator decisions: `stale_after_days`,
  `confidence_threshold`, `max_hop_depth`. The Inspector reads
  them; the rule file holds defaults; the CLI passes them.

Changing policy MUST NOT require changing the Kernel. The reverse
may be needed (rule needs new public API) — that path is governed
by Pillar 1.

### Pillar 4 — Falsability

Every Finding carries a `falsation: dict` that explains, in
machine-readable form, **the data change that would flip the
finding's `status`**. A Finding without meaningful falsation is a
finding the Inspector will not produce.

This pillar is the most distinctive property of the Inspector:
each finding is an *assertion*, not an *opinion*. The falsation
block belongs to the Finding so the rendered report is
self-contained — no external lookup is needed to verify a result.

### Pillar 5 — Findings, not decisions

The Inspector produces evidence. It does not:
- Conclude that the Kernel needs a schema change.
- Conclude that a new PI should be opened.
- Conclude that the operator should take any action.

Consumers (humans or downstream tools) read findings and decide.
The Inspector's vocabulary on a per-finding basis is one of:

- `status ∈ {pass, fail, skipped}`
- `severity ∈ {info, warning, fail}`

A single bot receiving the report can chart, alert, and store —
but it cannot, by reading the Inspector's output, decide that
the project needs a new architecture. That is preserved for the
epistemological layer.

## Discovering rules

A Rule module exposes a single `RULE = SomeRuleClass()` instance at
module level. The Inspector runtime can discover rules by importing
each module under `inspector/rules/`. A Rule conforms to the
protocol:

| Attribute | Type | Purpose |
|---|---|---|
| `id` | `str` | Stable identifier (e.g. `stale_entity`) |
| `version` | `str` | Semantic. Bump on breaking policy or schema |
| `consumes_api` | `tuple[str, ...]` | Public functions the rule reads |
| `consumes_entities` | `tuple` | Selection (`("all",)` or `("by_kind", "<k>")`) |
| `evaluate(api, policy, now, entity_ids=None)` | method | Returns `Iterable[Finding]` |

A rule that requires attributes not in this protocol is a v0.2
change.

## Verification recipe

```bash
PYTHONPATH=consumers/inspector python3 -m pytest \
    consumers/inspector/tests/test_inspector.py -v
```

Expect 9/9 green. A regression in any of them indicates a contract
change has been introduced without this document being updated.

## Evolution policy (frozen)

Any future change to `consumers/inspector/` MUST be classified into
exactly one of the following three categories. The classification is a
prerequisite for proposing the change.

| Category | Examples | Action |
|---|---|---|
| **New rule** | `low_confidence_dependency`, `cycles_invalid`, `missing_runs_on`, etc. | Implement one `Rule` module. **No contract change.** |
| **New policy** | Different `stale_after_days`, new severity thresholds, new TTL windows | External configuration that flows through `policy` across all existing rules. **No contract change.** |
| **Contract change** | Modify `Rule`, `Finding`, `KernelAPI`, or any documented invariant | Requires evidence: a *specific* rule that was impossible (not merely awkward) to implement with the current contract. Without that evidence, the change is rejected. |

The third category is exceptional. If it occurs, the proposal must
answer:

> What concrete rule could not be implemented under the existing
> contract? Document the attempted implementation, the obstacle, and
> why no consumer-side algorithm could bridge the gap.

If no such rule exists, the contract change lacks sufficient
evidence and stays unsubmitted.

## Contract Stability Index (CSI)

CSI = (number of rules implemented) / (contract changes to date)

This is an *architectural stability* metric, not a quality metric.
When the Inspector has 5 rules and 0 contract changes, CSI = infinity
in practice and means the v0.1 contract covered the first-order
design space. The first contract change after v0.1 freezes MUST be
justified by demonstrable incapacity, not by aesthetic preference.

Tracking the index is part of every commit touching `inspector/`:
the commit message records both `rules_implemented` and
`contract_changes`.

## What is NOT in this contract

- `inspector.cli` — operational, changes permitted without bumping v0.1.
- `inspector/__init__.py` — versions may roll up between releases.
- File layout (`inspector/rules/`, `inspector/evidence.py`) — internal.
- Internal helpers like `_parse_iso`, `_evidence_from_result` — internal.

These belong to the *implementation*, not the *contract*.
