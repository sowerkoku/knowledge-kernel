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

**Do not change in v1.x:**

| Surface | Identifier | Reason |
|---|---|---|
| Python package | `cmdb` | Public import path: `from cmdb.api import …` |
| Environment variable | `AGENT_CMDB_DATA_DIR` | Active installations depend on it |
| Default path | `~/agent-cmdb/...` | Backward-compatible default in `config.py`, `migrator.py` |
| CLI entry point | `cmdb` | Registered in `pyproject.toml` |
| Distribution name (already migrated) | `knowledge-kernel` | ✅ Done in v1.2 |

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

- [ ] v1.x has been stable for at least one minor release cycle
- [ ] At least one external downstream consumer has validated the API
- [ ] Migration guide is drafted (target: `docs/migration-v1-to-v2.md`)
- [ ] Telemetry confirms real-world adoption is non-zero

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
