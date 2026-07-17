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
- Internal optimizations (in-memory indexes, caching)
- Documentation improvements
- New tools added on top of existing API (additive; non-overriding)
- Dataset content additions (entities can be added; existing IDs are immutable)

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

**Priorities for v1.x iteration:**

1. **Adoption pathway** — Can another agent use the Kernel without additional
   explanation? Onboarding friction is a real measurement.
2. **Natural API feel** — Do the function names reflect the questions agents ask?
   (`cmdb_exists` is readable; `cmdb_assert` is ambiguous.)
3. **Query frequency observation** — Which tools get called most? Idle tools are
   design noise.
4. **Performance bottlenecks** — Where does the system introduce latency?
   Address non-breaking optimizations first.
5. **Missing functions** — What adjacent capabilities are needed but absent?

**Signals to collect (telemetry-driven):**

- Frequency of each `cmdb_*` tool invocation
- Ratio of `cmdb_exists` calls that lead to `cmdb_get`
- Number of `assert_success=False` results (signal of missing entities)
- Time-to-answer (latency percentile per operation)
- Number of distinct agent integrations active

These signals — not aesthetic code reviews — drive the next major version.

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

Do **not** start v2.0 work until **all** of the following hold:

**Time-based:**

- [ ] v1.x has been stable for at least one minor release cycle (≥ v1.3.0)

**Adoption-based (telemetry signals):**

- [ ] At least one external downstream consumer integrated without assistance
- [ ] ≥ 100 queries logged in telemetry (proves real usage, not just smoke tests)
- [ ] ≥ 3 distinct `cmdb_*` tools called in production (proves breadth of use)
- [ ] No support tickets / unknown blockers in last minor cycle

**Documentation-based:**

- [ ] Migration guide drafted (target: `docs/migration-v1-to-v2.md`) — **stub created**, needs changelog anchors and rollback verified.
- [ ] Changelog template populated with concrete breaking changes
- [ ] Release notes explain _why_ each breaking change is necessary (user value, not aesthetics)

**Architectural-based:**

- [ ] API surface stable for ≥ 1 minor cycle with no breaking additions
- [ ] Telemetry confirms performance bottlenecks are addressed where possible
- [ ] At least one architectural improvement has been completed in v1.x without regression

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
