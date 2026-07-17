# Runtime Compatibility Cleanup — Roadmap

> **Status:** Draft / proposed for v2.0 milestone
> **Author:** Project maintainers
> **Created:** 2026-07-16
> **Target version:** `2.0.0`

---

## Context

During the **v1.2 documentation rewrite**, the project's public brand was migrated
from `Agent-CMDB` to `Knowledge Kernel`. All *user-facing* naming — README,
docstrings, observable comments — was updated.

However, several *technical* identifiers remain tied to the previous identity.
They were intentionally left in place to preserve runtime compatibility:

- Default filesystem paths
- Environment variable names
- Internal package directory
- Build artifact metadata

This document tracks those remnants and defines the criteria for cleaning them in
a single, controlled breaking release.

---

## v1.x — Stability Window

**Current version:** `1.2.0` (frozen on this commit).

The v1.x line accepts only:

- Bug fixes
- Security patches
- Documentation improvements
- Performance improvements that preserve compatibility
- New tools that don't break existing contracts (additive only)

**Frozen contracts — do not change in v1.x:**

| Surface | Current state | Reason |
|---|---|---|
| **Public API** | `cmdb.api` import path; functions `cmdb_get`, `cmdb_exists`, `cmdb_impact`, `cmdb_context`, `cmdb_assert`, `cmdb_search`, `cmdb_list`, `cmdb_validate`, `cmdb_reload`, `cmdb_migrate`, `cmdb_engine_info`, `cmdb_stats` | External agents depend on these signatures |
| **YAML entity schema** | v2 schema; fields `id`, `kind`, `status`, `metadata`, `relations`, `evidence` | 36 entities validated against this schema |
| **Relations contract** | `runs_on`, `depends_on`, `part_of` | Minimum-relations principle; aliases prohibited in v1.x |
| **Evidence/provenance contract** | `Evidence` model: `source`, `observed_at`, `ttl_seconds`, `confidence`, `confidence_basis`, `validation_method` | Consumers parse this shape |
| **Environment variables** | `CMDB_DATA_DIR`, `AGENT_CMDB_DATA_DIR` | Active installations depend on them |
| **Dataset structure** | `~/knowledge/knowledge-kernel/<kind>/<entity_id>.yaml` | Backward-compatible default in `config.py`, `migrator.py` |
| **Internal package** | Module name `cmdb` | Public import path: `from cmdb.api import …` |
| **CLI entry point** | `cmdb` command | Registered in `pyproject.toml` |
| **Hermes skill contract** | `~/.hermes/skills/knowledge-kernel/SKILL.md` | Sync test enforces parity with `integrations/hermes/SKILL.md` |
| **Distribution name** (already migrated) | `knowledge-kernel` | ✅ Done in v1.2 |

**Allowed in v1.x:**

- Bug fixes
- Internal optimizations (in-memory indexes, caching, faster lookups)
- Documentation improvements
- New tools added on top of existing API (additive; non-overriding)
- Dataset content additions (entities can be added; existing IDs are immutable)
- Telemetry instrumentation (required for adoption evidence)
- Performance improvements (non-breaking)
- CLI output enhancements (formatting, verbosity, human readability)

**Frozen ≠ Stagnant**

Frozen contracts mean **consumers can rely on the surface** without breaking changes.
They do not freeze internal improvements, new capabilities added above the surface,
or documentation deepening. v1.x can (and should) accumulate evidence of value
through adoption, performance enhancements, and tool expansions — all without
violating the contracts listed above.

The design goal: **maximize value delivered to users while minimizing churn for
existing adopters.** Internal upgrades that don't leak through the API are
encouraged, not blocked.

### Parallel structure: Knowledge Kernel epistemology ↔ Development governance

The Knowledge Kernel implements a governance model based on:

- **Evidence → Fact** (observation becomes a grounded truth)
- **Provenance** (trace why the fact is trusted)
- **Human curation** (gate to prevent spurious discoveries)
- **Deterministic reasoning** (repeatable inference)

This roadmap applies the same philosophy to **product development**:

- **Evidence of adoption → Decision to release v2.0**
- **Justification** (migration guide explains **why** each breaking change is necessary)
- **Maintainer curation** (decision to liberate v2.0, not a checkbox list)
- **Governed evolution** (change is deliberate, not driven by arbitrary thresholds)

**Design symmetry:** When the product model and the product's own governance
are structurally aligned, coherence signals maturity. This is not accidental.

### Inflection Point: Invention → Validation

The project's history follows five stages, each resolving questions the previous
stage could not answer:

| Stage | Core Question | Status in v1.2.0 |
|---|---|---|
| **1. Modeling** | What entities and relations exist? | Resolved (36 entities, v2 schema) |
| **2. Governance** | What evidence validates each fact? | Resolved (8 axioms, evidence model) |
| **3. Architecture** | What is the public contract? | Resolved (`cmdb.api`, 10 frozen surfaces) |
| **4. Product** | Is it packaged, documented, stable? | **Resolved** (v1.2 release, docs complete) |
| **5. Adoption** | Do other agents use it without modification? | **Current active stage** |

**Decision recorded:** Entering v1.x stability means stage 4 is declared **settled**. Returning to stages 1–4 questions ("should we redesign the schema?", "should we restructure the API?", "should we change the relations?") now requires **evidence from adoption** that the current design is inadequate — not abstract debate. This prevents infinite re-litigation.

---

**Prohibited in v1.x:**

- Renaming any field in frozen contracts
- Adding new relation types (would change the relations contract)
- Changing evidence model fields
- Changing dataset folder layout
- Renaming env vars
- Modifying the public API surface

---

## Active Focus — Adoption, Performance, Experience

Until v2.0 work begins, the project's primary risk is **product risk**, not
architectural risk. Design questions ("is the epistemic model correct?") are
considered settled for the v1.x line.

### Project evolution — where we have been

Each prior iteration resolved a question that the previous stage could not:

1. **Modeling** — Define entities and relations.
2. **Governance** — Establish evidence, provenance, and operational rules.
3. **Architecture** — Lock the Knowledge Kernel contract.
4. **Product** — Package the API, documentation, identity, and stability.
5. **Adoption** — Demonstrate that other agents actually use it.

The transition from **Product → Adoption** is the current phase. Re-entering
earlier stages (refining models, redesigning governance, restructuring
architecture) would mean the prior work was not actually settled. The value of
this stage comes from observing real consumer usage, not from further
in-abstracto design work.

### Priorities for v1.x iteration

1. **Adoption pathway** — Can another agent use the Kernel without additional
   explanation? Onboarding friction is a real measurement.
2. **Natural API feel** — Do the function names reflect the questions agents ask?
   (`cmdb_exists` is readable; `cmdb_assert` is ambiguous.)
3. **Query frequency observation** — Which tools get called most? Idle tools are
   design noise.
4. **Performance bottlenecks** — Where does the system introduce latency?
   Address non-breaking optimizations first.
5. **Missing functions** — What adjacent capabilities are needed but absent?

### Signals to collect (telemetry-driven)

- Frequency of each `cmdb_*` tool invocation
- Ratio of `cmdb_exists` calls that lead to `cmdb_get`
- Number of `assert_success=False` results (signal of missing entities)
- Time-to-answer (latency percentile per operation)
- Number of distinct agent integrations active

These signals — not aesthetic code reviews — drive the next major version.
Quantitative metrics are useful for tracking progress, but they become
evidence only when paired with qualitative confirmation (e.g., a real
consumer report).

---

## v2.0 — Compatibility Cleanup

### Scope of breaking changes

1. **Introduce `KNOWLEDGE_KERNEL_DATA_DIR`** as the canonical environment variable.
   - Keep `AGENT_CMDB_DATA_DIR` with a `DeprecationWarning` for the full v2.x cycle.
   - Remove `AGENT_CMDB_DATA_DIR` in `v3.0`.

2. **Change default paths** from `~/agent-cmdb/...` to `~/knowledge-kernel/...`.
   - Apply to `cmdb/config.py` (`cache_dir`), `cmdb/migrator.py` (`entities_dir`).
   - Add an explicit migration note in the changelog.

3. **Regenerate `.egg-info/`** with the correct `Name: knowledge-kernel` and
   update `PKG-INFO` references to point at `github.com/sowerkoku/knowledge-kernel`.

4. **Update `cmdb/registry_migrator.py`** argparse descriptions and docstrings
   that still reference the old brand internally.

5. **Update `tests/test_acceptance.py`** examples and comments that mention
   the old paths (cosmetic; non-breaking).

### Out of scope (intentional non-changes)

- Python module name `cmdb` — stable. Renaming to `knowledge_kernel` is a
  separate `v3.0` decision.
- Public API function names (`cmdb_get`, `cmdb_exists`, `cmdb_impact`, etc.) — stable.
- CLI command names (`cmdb exists`, `cmdb get`) — stable.

---

## Activation Criteria

v2.0 work begins only when **evidence shows** the v1.x line has stabilized and
real adoption has generated enough signal to design migration confidently. These
are evidence-based gates, not arbitrary numeric thresholds. Numeric metrics may
help quantify each gate, but they alone are not sufficient.

### Gates — each must be evidenced

**1. API stability evidenced in real use**

Evidence that the public API is stable across real usage patterns — not just
declared frozen. This may include telemetry logs, integration reviews from
external users, or signed-off pilot integrations. Signing on the dotted line of
"frozen contract" without actual consumers is not sufficient.

**2. External consumers using the contract without modifications**

Evidence of at least one external agent or system consuming the public API
*as documented* — without patches, forks, or layers of compatibility shims. If
consumers need a workaround, the contract is not actually stable.

**3. Main query patterns identified and covered**

Evidence that the primary use cases are understood: which `cmdb_*` tools are
called most, what data shapes they return, what failures occur, and whether the
public API expresses them naturally. This evidence drives the *scope* of v2.0:
breaking changes should reflect known usage, not hypothetical improvements.

**4. Pending breaking changes clearly defined and justified**

Each breaking change planned for v2.0 must name:
- **What** breaks (specific field, env var, path, function name).
- **Who** is affected (consumers, scripts, deployments).
- **Why** the change is necessary (user value, not aesthetic preference).
- **Migration path** (concrete steps users must take).

Cosmetic renames with no user value are not v2.0 candidates. They may wait indefinitely.

**5. Migration guide complete and validated**

The v2.0 migration guide must be:
- Drafted.
- Validated against at least one real consumer (internal team review, external
  pilot, or dry-run walkthrough).
- Verified to be **safe and reversible** (a rollback path must exist for at
  least one minor cycle post-release).

### Notes on framing

These gates are framed as **evidence** rather than **numbers** because
quantitative thresholds (e.g., "100 queries", "3 distinct tools", "1 minor
cycle") can be met without the underlying stability being real. A 100-query
log can hide a design flaw. A single user with a clear workload can surface
what 100 smoke tests cannot. The intent is *evidence of stability*, not
*targets to hit*.

If desired, quantitative metrics can be associated with each gate as
**indicative** measurements — helpful for tracking progress — but they should
not be mistaken for the gate itself.

---

## Decision Criterion (from maintainer discussion, 2026-07-16)

> **"Does this change bring value to the user, or only improve code aesthetics?"**
>
> If only aesthetics → postpone.
>
> If user-facing value → schedule for the next major version.

This criterion replaces the prior heuristic of "whenever we notice a remnant".
Cosmetic cleanups introduce churn without delivering value; they should wait for
a v2.0 cycle that bundles all of them.

---

## Open Questions

1. Should `cmdb` module rename to `knowledge_kernel` in v2.0 or v3.0?
   - Pro: matches the public brand.
   - Con: largest possible breaking change in the import surface.

2. Should the CLI command rename from `cmdb` to `kk` or `kernel`?
   - Pro: discoverability.
   - Con: every shell alias and script breaks.

3. How long is the deprecation window for `AGENT_CMDB_DATA_DIR`?
   - Options: one v2.x minor, full v2.x cycle, until v3.0.

---

## Changelog Anchoring

When v2.0 ships, the release notes must include:

```markdown
## BREAKING CHANGES (v1.x → v2.0)

- **Environment variable:** `AGENT_CMDB_DATA_DIR` is deprecated.
  - New canonical name: `KNOWLEDGE_KERNEL_DATA_DIR`.
  - Old name still works with a `DeprecationWarning`.
  - Hard removal scheduled for v3.0.

- **Default paths:** changed from `~/agent-cmdb/` to `~/knowledge-kernel/`.
  - Existing installations are unaffected if they set `*_DATA_DIR` explicitly.
  - See `docs/migration-v1-to-v2.md` for details.
```
