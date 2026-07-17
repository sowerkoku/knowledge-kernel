# Migration Guide — v1.x to v2.0

> **Draft status:** placeholder
> **Target release:** v2.0.0
> **Last updated:** 2026-07-16

---

## Overview

This guide documents the breaking changes between the **v1.x stability line** and
**v2.0** (the Compatibility Cleanup release).

**v1.x line:** stable, frozen API surface, frozen YAML schema, frozen relations.

**v2.0 line:** internal identifiers aligned to the public `Knowledge Kernel` brand.

---

## Who this affects

You need to act if:

- You depend on `from cmdb.api import ...` (public API — **still works**)
- You set `AGENT_CMDB_DATA_DIR` explicitly
- You rely on default paths (e.g., `~/.cache/agent-cmdb/`)
- You call `cmdb_get()`, `cmdb_exists()`, etc. programmatically (**still works**)

**You do NOT need to act if:**

- You only use the CLI (`cmdb ...`) with explicit paths
- You set `CMDB_DATA_DIR` explicitly (**still works** — no deprecation)

---

## Breaking Changes

### 1. Environment Variable: `AGENT_CMDB_DATA_DIR` → `KNOWLEDGE_KERNEL_DATA_DIR`

**What changed:**

The canonical environment variable name now reflects the public brand.

**Backward compatibility:**

`AGENT_CMDB_DATA_DIR` continues to work in v2.x with a `DeprecationWarning`
logged on each access.

**Hard removal:** Scheduled for v3.0.

**Migration steps:**

1. Update shell profiles, scripts, and Docker env files:
   ```diff
   - export AGENT_CMDB_DATA_DIR=~/knowledge/knowledge-kernel
   + export KNOWLEDGE_KERNEL_DATA_DIR=~/knowledge/knowledge-kernel
   ```
2. Verify:
   ```bash
   cmdb exists ollama  # should succeed without warnings
  ```
3. Expected warning (v2.x only):
   ```
   DeprecationWarning: `AGENT_CMDB_DATA_DIR` is deprecated and will be removed in v3.0. Use `KNOWLEDGE_KERNEL_DATA_DIR` instead.
   ```

**Why change:** Consistency between public brand and internal identifiers.

---

### 2. Default Paths: `~/agent-cmdb/` → `~/knowledge-kernel/`

**What changed:**

The system's default directories now use the `knowledge-kernel` name.

| Directory | Old (v1.x) | New (v2.0+) |
|---|---|---|
| Dataset | `~/knowledge/agent-cmdb/` | `~/knowledge/knowledge-kernel/` |
| Cache | `~/.cache/agent-cmdb/` | `~/.cache/knowledge-kernel/` |
| Legacy shared (not used in v1.x) | `~/.local/share/agent-cmdb/` | `~/.local/share/knowledge-kernel/` |

**Backward compatibility:**

If you explicitly set `*_DATA_DIR` env vars, you are unaffected.

If you rely on **default paths** and do **not** upgrade, you are unaffected.

**Migration path (existing installations):**

Option A — **Move your data** (recommended):

```bash
mv ~/knowledge/agent-cmdb ~/knowledge/knowledge-kernel
mv ~/.cache/agent-cmdb ~/.cache/knowledge-kernel
```

Option B — **Pin your env vars** (if you prefer directories with legacy name):

```bash
export KNOWLEDGE_KERNEL_DATA_DIR=~/knowledge/agent-cmdb
export CMDB_CACHE_DIR=~/.cache/agent-cmdb
```

**Verify after migration:**

```bash
cmdb get ollama
cmdb validate
```

The second command should confirm `valid=True, errors=0`.

---

### 3. Package Distribution Name (already migrated in v1.2)

**Change:**

`pyproject.toml` renamed to `knowledge-kernel` in v1.2.0.

**Impact:**

- `pip install knowledge-kernel` works ✅
- Old `agent-cmdb` wheel names are no longer produced (but remain on PyPI as historical artifacts).
- `.egg-info/` regeneration required after fresh install.

**No action needed** if you install from source or via `pip install -e .`

---

## Unchanged (Non-breaking)

**Not affected by this release:**

- Public API contract: `cmdb_get()`, `cmdb_exists()`, `cmdb_impact()`, etc.
- YAML entity schema: fields `id`, `kind`, `status`, `metadata`, `relations`, `evidence`
- Relations: `runs_on`, `depends_on`, `part_of`
- Evidence model fields: `source`, `observed_at`, `ttl_seconds`, `confidence`, etc.
- Python module name: `cmdb`
- CLI command names: `cmdb exists`, `cmdb get`, `cmdb validate`
- Hercules skill contract: `SKILL.md` sync with `integrations/hermes/SKILL.md`

---

## Rollback Procedure

If you encounter regressions after upgrading to v2.0:

1. Keep your data in the new location.
2. Downgrade to v1.3.x:
   ```bash
   pip install knowledge-kernel==1.3.0
   ```
3. Pin your path explicitly (prevents default-path change):
   ```bash
   export KNOWLEDGE_KERNEL_DATA_DIR=~/knowledge/knowledge-kernel
   ```

Rollback is safe because data layout is identical (only env var name changed).

---

## FAQ

**Q: Do I need to change my imports from `cmdb`?**

No. The module name `cmdb` is intentionally stable. This change is deferred to v3.0.

**Q: My agent uses `cmdb_exists()` — will this break?**

No. The public function signatures are frozen for v1.x and v2.x.

**Q: I use `AGENT_CMDB_DATA_DIR` in production — do I need to change it now?**

v2.x will warn but not break. Set a calendar reminder to change it before v3.0.

**Q: Does the YAML schema change?**

No. The entity schema is frozen. New fields or relation types would require v3.0.

---

## Open Questions (for v2.0± discussion)

- Should `cmdb` module rename to `knowledge_kernel` in v2.0 or delay to v3.0?
- Should CLI `cmdb` command rename to `kk` or `kernel`?
- What is the deprecation window duration for `AGENT_CMDB_DATA_DIR`?
  - Options: one v2.x minor, full v2.x cycle, until v3.0.

---

## Changelog anchors for v2.0 release notes

```markdown
## Breaking Changes (v1.x → v2.0)

- **Environment variable:** `AGENT_CMDB_DATA_DIR` deprecated.
  - New: `KNOWLEDGE_KERNEL_DATA_DIR`.
  - Old name works with warning until v3.0.
- **Default paths:** renamed to `knowledge-kernel`.
  - `~/knowledge/agent-cmdb/` → `~/knowledge/knowledge-kernel/`
  - `~/.cache/agent-cmdb/` → `~/.cache/knowledge-kernel/`
- **Package distribution:** `knowledge-kernel` (since v1.2; historical `agent-cmdb` wheels deprecated).

## Non-breaking Improvements

- Documentation: adoption roadmap, frozen contracts list.
- Performance: internal optimizations (no API impact).
- Telemetry added (opt-in; privacy-preserving).
```

---

*This document lives at [`docs/migration-v1-to-v2.md`](./migration-v1-to-v2.md) in the repository.*