# Project Constitution — knowledge-kernel

> **Purpose:** This Constitution governs the **evolution of the project itself**.
> It does **not** define the factual model, evidence model, or API contracts of
> the Knowledge Kernel product. Those are governed by [`governance.md`](./governance.md),
> [`philosophy.md`](./philosophy.md), and [`architecture.md`](./architecture.md).

---

## 1. Purpose

This document establishes the principles and decision rules that govern how the
**knowledge-kernel project** evolves over time.

**What this governs:**
- When and how the project's public contracts may change
- When architectural decisions may be revisited
- What constitutes valid evidence for change
- How compatibility is treated as a product feature

**What this does NOT govern:**
- What entities belong in the Knowledge Kernel (see `governance.md`)
- The epistemic principles of the Kernel (see `philosophy.md`)
- The API surface or data model contracts (see `architecture.md`, `domain-model.md`)

**Amendments:** This Constitution may only be amended when there is **evidence**
that one of its principles no longer serves the project's purpose of providing
a deterministic, evidence-backed factual substrate for AI agents. Abstract
preference or aesthetic preference alone is insufficient.

---

## 2. Constitutional Principles

These five principles are the foundation of all project decisions:

### 2.1 Evidence before change

Architectural or breaking changes require **empirical evidence** from real
adoption — not speculation, intuition, or hypothetical improvements. Evidence
includes: telemetry logs, user reports, integration failures, or performance
bottlenecks observed in production.

### 2.2 Public contracts are harder to change than implementations

The public API, YAML schema, relations contract, and evidenced provenance
model are **frozen** by default. Internal implementations may evolve freely
as long as they preserve these contracts. Breaking a public contract requires
evidence that the contract itself is inadequate — not merely that an
alternative would be elegant.

### 2.3 Determinism is preserved unless intentionally broken

Every change must preserve deterministic behavior: same input → same output.
Non-deterministic changes (e.g., reordering, probabilistic behavior,
time-dependent outputs) are prohibited unless explicitly justified and
documented as a breaking change in a major version.

### 2.4 Compatibility is a product feature

Backward compatibility is not "technical debt" — it is a **product feature**
that enables adoption. Breaking changes are costly for users; they must
deliver user-facing value, not just internal cleanliness. Cosmetic renames
without user value are indefinitely deferred.

### 2.5 Adoption validates architecture

An architecture is validated by **real adoption**, not by design elegance.
If external consumers use the public contracts without modification, the
architecture is working. If they require workarounds, forks, or shims, the
architecture has a problem — regardless of how elegant the design appears
on paper.

---

## 3. Decision Rule

**Architectural decisions require evidence.**

A decision to change a frozen contract, add a breaking change, or reopen a
settled design question must be accompanied by:

1. **What** the evidence is (telemetry log, user report, benchmark).
2. **Why** the current design is inadequate for the observed use case.
3. **What** user value the change delivers (not aesthetic preference).
4. **How** users will migrate (concrete steps, rollback path).

**Reopening settled decisions requires empirical evidence.**

Once a design question is resolved (e.g., "What is the public API?", "What
relations are supported?", "What is the evidence model?"), it may not be
revisited unless adoption evidence demonstrates that the current design is
inadequate for real use cases. Abstract debate alone is insufficient.

---

## 4. Project Evolution

The project's history follows five stages, each resolving questions the
previous stage could not answer:

| Stage | Core Question | Status |
|---|---|---|
| **1. Modeling** | What entities and relations exist? | Resolved (v1.2: 36 entities, v2 schema) |
| **2. Governance** | What evidence validates each fact? | Resolved (8 axioms, evidence model) |
| **3. Architecture** | What is the public contract? | Resolved (`cmdb.api`, 10 frozen surfaces) |
| **4. Product** | Is it packaged, documented, stable? | **Resolved** (v1.2 release, docs complete) |
| **5. Adoption** | Do other agents use it without modification? | **Current active stage** |

**Decision recorded:** Entering v1.x stability means stage 4 is declared
**settled**. Returning to stages 1–4 questions requires **evidence from
adoption** that the current design is inadequate — not abstract debate.
This prevents infinite re-litigation of settled design questions.

---

## 5. Amendments

This Constitution is a **stable document**. It should not change with every
iteration. Amendments require:

1. **Evidence** that one of the five principles no longer serves the project's
   purpose (e.g., adoption blocked by a principle, user harm demonstrated).
2. **Explicit documentation** of why the principle is being changed.
3. **Public announcement** in release notes, with rationale.
4. **Waiting period** of at least one minor release cycle between proposal
   and adoption (to allow community feedback).

**Principle:** The Constitution exists to prevent hasty changes driven by
novelty or aesthetic preference. It should be amended only when the weight
of evidence makes it clear that the principle itself — not just its
application — is flawed.

---

## References

- [`governance.md`](./governance.md) — What facts enter the Knowledge Kernel
- [`philosophy.md`](./philosophy.md) — Epistemic principles of the Kernel
- [`roadmap-compatibility.md`](./roadmap-compatibility.md) — v1.x stability window, v2.0 activation gates
- [`migration-v1-to-v2.md`](./migration-v1-to-v2.md) — Migration guide for future breaking changes

---

*This Constitution was adopted on 2026-07-16, following the v1.2 release and
the迁移 from "Agent-CMDB" to "Knowledge Kernel" branding. It codifies the
decision to separate product governance from project governance, and to
require evidence before revisiting settled design questions.*