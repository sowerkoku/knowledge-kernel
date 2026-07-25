---
name: knowledge-kernel
description: Knowledge Kernel — a deterministic, evidence-backed source of truth for AI agents. Stores verified facts, evidence, relationships, and freshness. Use this when an agent needs to know infrastructure, software, endpoints, dependencies, agents, or projects — anything grounded in empirical reality.
category: infrastructure
version: 2.0.0
author: Carlos Cáceres
license: MIT
tags: [grounding, knowledge-kernel, deterministic-factual-substrate, facts, infrastructure, hallucination-prevention, endpoint-identity]
---

# knowledge-kernel Skill

> **Decide a question with grounding:**

> 1. Does the Kernel have it? Query it.
> 2. Does the Kernel have the path to observe it? Query the path, then observe.
> 3. Otherwise: say "I don't have grounds to answer."

---

## Measurement planes

The ecosystem tracks three distinct planes. Conflating them loses
information about which layer is under pressure:

| Plane | What it measures | Indicator | Where |
|---|---|---|---|
| **Inspector contract** | Is the Inspector's Rule/Finding/KernelAPI contract sufficient? | CSI = rules : contract_changes | `consumers/inspector/CSI.md` |
| **Kernel data model** | Does the model express the phenomena the Inspector needs? | EP (Expressivity Pressure) events | `consumers/inspector/CSI.md` + `NOTES.md` |
| **Dataset health** | What is the current state of the stored knowledge? | Finding counts per run | JSON reports via `consumers/inspector/tools/runs_diff.py` |

CSI is expressed as `N : M` (rules : contract_changes), never as `∞`.
PI opening for EP events is **recurrence-based**, not threshold-based.
See [`references/inspector-pattern.md`](references/inspector-pattern.md) for
the full Inspector methodology including the EP recurrence protocol.

---

## 1. What is the Knowledge Kernel?

A deterministic, reproducible, auditable factual substrate for AI agents.

It stores:

- **facts** — verified entities (assets, software, endpoints, agents, projects)
- **evidence** — why each fact is trusted (`source`, `observed_at`, `confidence`)
- **relationships** — how facts connect (`runs_on`, `uses`, `exposed_by`, etc.)
- **freshness** — whether each fact is still valid

One canonical home per concept. Many agents query it. Always choose it
over inference, over RAG, and over conversation memory.

---

## 2. Where does everything live?

### Canonical paths

| What                    | Where                                           |
|-------------------------|-------------------------------------------------|
| Repo (code, package)    | `<repo-root>` (`~/knowledge-kernel/`)           |
| Skill location          | `~/.hermes/skills/knowledge-kernel/`            |
| Skill entrypoint        | `~/.hermes/skills/knowledge-kernel/SKILL.md` (this file) |
| Dataset (production)    | `<dataset-root>` (YAML entities)                |
| **Documentation**       | `<repo-root>/docs/`                             |
| Hermes tools (wrappers) | `~/.hermes/skills/knowledge-kernel/tools/`       |
| Tests                   | `<repo-root>/tests/`                            |

### Structural layers

The repo is organized into three layers with distinct dependencies:

```
kernel/        ← the model; no dependencies upward
consumers/     ← framework-agnostic consumers of the public API
                inspector/, telemetry/ — run from any agent or CI
integrations/  ← platform-specific adapters; depend on external platform
                hermes/ — depends on Hermes
```

**`consumers/` vs `integrations/`** is an architectural boundary enforced
by `tests/test_consumers_boundary.py`. A consumer must not import from
any `integrations/*` package (hermes, openclaw, etc.) or from the
integrations layer itself. If a component needs a platform, it belongs
in `integrations/`, not `consumers/`. This keeps `consumers/` reusable
across agents.

### Configuration

```bash
# Dataset location
export CMDB_DATA_DIR=<dataset-root>

# Install the package (run once)
<repo-venv>/bin/python3 -m pip install -e <repo-root>

# Verify
<repo-venv>/bin/python3 -c "from cmdb.api import cmdb_get; print('✓')"
```

### Pitfall: never hardcode `data_dir` inside Python

All modules read from `get_config().data_dir`. See
`docs/pitfalls/default-path-drift.md`.

---

## 3. What APIs exist, and when to use each?

The public API is defined by `cmdb/api.py:__all__` — that file is the
normative source. This skill lists the entry points; for signatures,
examples, and return-type details, read the canonical reference.

```python
from cmdb.api import (
    # Query
    cmdb_exists,    # Existence check before any factual claim
    cmdb_get,       # Full entity with evidence + relations
    cmdb_search,    # Free-text search by name/desc/tags
    cmdb_list,      # Filtered enumeration by kind/domain/status
    # Decisions
    cmdb_impact,    # Dependency graph (BEFORE modifying anything)
    cmdb_assert,    # Binary assertion for decision points
    cmdb_context,   # Pre-packaged agent context (call once at start)
    # Validation
    cmdb_validate,  # Health check on the whole Kernel
    # Operational introspection
    cmdb_engine_info,  # Generation counter, dataset_hash, index sizes
    cmdb_stats,        # Entity counts by kind, relation total, dataset hash
)
```

Ten public functions. Anything not exported by `cmdb.api.__all__` is
internal, regardless of where else it appears in the documentation.

> **API Reference**: The canonical, complete documentation of the public
> API (all functions, return types, usage patterns, best practices,
> anti-patterns, compatibility) lives in
> [`docs/api-python.md`](../knowledge-kernel/docs/api-python.md).

### What is NOT in the public API

- `cmdb_reload` — CLI maintenance tool at `tools/cmdb_reload.py`. Forces
  index invalidation. Side-effect, not query.
- `cmdb_migrate_dry_run`, `cmdb_migrate_apply` — internal submodule
  (`cmdb/migrator.py`). Migration primitives invoked via CLI.

**Decision rule on documentation drift.** If this SKILL.md and
`docs/api-python.md` disagree, follow `cmdb/api.py:__all__` and update
the docs to match. Documentation converges toward code, not the reverse.

### Decision flow

```
Question arrives
  │
  ├─ Can the Kernel answer directly?
  │   ├─ Yes → cmdb_get / cmdb_list / cmdb_search
  │   │        → Report fact with evidence.confidence
  │   │
  │   └─ No (needs external observation)
  │       ├─ Does the Kernel give the path? (endpoint, host, credentials)
  │       │   ├─ Yes → use Kernel facts → execute tool → report
  │       │   └─ No → "I don't have grounds to answer."
```

### Anti-patterns

- Do **not** infer facts from entity IDs (`server-192-168-1-52` does **not**
  encode the IP — read `metadata.primary_ip`)
- Do **not** count entities by string-match on IDs (`cmdb_list(kind=...)` is
  the stable category)
- Do **not** treat missing facts as false — say "unverified"
- Do **not** modify anything without first running `cmdb_impact(id)`
- Do **not** commit infrastructure-specific data to the public repo (IPs, hostnames, MACs, PIDs, telemetry). See
  [`references/repository-instance-boundary.md`](references/repository-instance-boundary.md) for the security sanitization workflow.
- Do **not** add alarmist notes to README after cleanup — silent removal is
  preferred over drawing attention to historical data no longer in HEAD.
- Do **not** store bare (unquoted) ISO dates in YAML `metadata.*` fields. PyYAML parses them as `datetime.date` objects. When `_compute_entity_hash()` calls `json.dumps()`, it crashes with `TypeError: Object of type date is not JSON serializable`. Always quote dates in YAML: `started: "2026-07-06"` not `started: 2026-07-06`. Fix in commit `c956cfe` (`cmdb/query.py: _json_default` serializer).
- Do **not** treat `~/.hermes/skills/knowledge-kernel/` as the source of truth. This directory has **no git tracking**. Any non-git tool (Hermes process, cron job, external script) that writes there causes the SKILL.md and tools to drift from the git-tracked canonical source in `~/knowledge-kernel/integrations/hermes/`. **Sync direction is always: repo → skill.** See [`references/skill-repo-sync.md`](references/skill-repo-sync.md).
- Do **not** state a change as done until evidence exists. `"Edición lista"` or `"Convergencia demostrada"` are claims, not facts. When a change is claimed, show `git diff`, byte hashes, or test output — not a narrative description. The next agent must be able to verify the claim without trusting the speaker. See [`references/public-api-audit-jul-2026.md`](references/public-api-audit-jul-2026.md) for the worked example (2026-07-24, commits `e0e9d64` → `7935cae`).

---

## 4. Executable Tools

Beyond the Python API, the skill ships standalone tools for operational
tasks. All accept `CMDB_DATA_DIR` env var (defaults to `~/knowledge/knowledge-kernel`).
Run with `python3 <tool.py>` from any directory.

### Observability — health & metrics

| Tool | What it answers | When to use |
|------|----------------|-------------|
| `kpi.py` | DQS (quality), FFR (freshness), entity breakdown by kind, validation result | Periodic health check. Run before and after any bulk change. |
| `cmdb_stats.py` | Entity count, relation count, per-kind breakdown, dataset hash | Quick snapshot — lighter than `kpi.py`, no validation step. |
| `cmdb_engine_info.py` | Generation counter, reload speed, last reload timestamp, index sizes | Debug why a query returns stale data. Confirm engine reloaded after edits. |

### Query — reading the Kernel

| Tool | What it answers | When to use |
|------|----------------|-------------|
| `cmdb_exists.py <id>` | Does entity X exist? | **Always** — before making any factual claim. |
| `cmdb_get.py <id>` | Full entity + evidence + relations | Deep reasoning about specific entity. |
| `cmdb_impact.py <id>` | Dependency graph: what breaks if X fails? | **Before modifying or deleting any entity.** |
| `cmdb_context.py <id>` | Pre-packaged context bundle for agent startup | Call once per agent session to prime the context. |

### Decision — binary gates

| Tool | What it answers | When to use |
|------|----------------|-------------|
| `cmdb_assert.py <id> <kind> <status>` | Binary: is entity X of kind Y with status Z? | Gates in CI/CD, pre-commit checks, automation decision points. |
| `cmdb_validate.py` | Full dataset health: errors, warnings | Before committing YAML changes, before push, as part of cron health job. |

### Maintenance — keeping the Kernel current

| Tool | What it answers | When to use |
|------|----------------|-------------|
| `cmdb_reload.py` | Did indexes rebuild? Time taken? New hash? | **After editing YAML directly** — the engine caches indexes; this forces rebuild. |
| `grounding_pilot.py` | KAR (kernel adoption rate), FGR (grounding rate) per category | Measure how often the agent chooses the Kernel over inference. Run in OBSERVE mode. |
| `run_pilot.py` | Runs the full grounding pilot suite | Periodic measurement cadence. Produces reproducible grounding metrics. |

### Quick reference

```bash
# Health snapshot
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 ~/.hermes/skills/knowledge-kernel/tools/kpi.py

# Fast existence check (no full entity load)
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 ~/.hermes/skills/knowledge-kernel/tools/cmdb_exists.py ollama

# Impact analysis before touching anything
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 ~/.hermes/skills/knowledge-kernel/tools/cmdb_impact.py server-192-168-1-53

# Reload after YAML edit
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 ~/.hermes/skills/knowledge-kernel/tools/cmdb_reload.py

# Dataset stats (lightweight)
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 ~/.hermes/skills/knowledge-kernel/tools/cmdb_stats.py

# Engine telemetry
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 ~/.hermes/skills/knowledge-kernel/tools/cmdb_engine_info.py
```

> The Python API (`from cmdb.api import cmdb_get, ...`) covers all query and
> decision functions programmatically. The tools above are CLI wrappers around
> the same API — use whichever is more convenient.

---

## 5. Contract — what must never break?

These are **permanent invariants**. Every change in the codebase respects them.

### Invariant 0 — One Responsibility, One Canonical Home

A fact lives in exactly one place. The Kernel is the canonical home of
facts. RAG indexes facts from the Kernel. Memory stores user preferences,
not facts. Conversations are ephemeral.

### Invariant 1 — Code ≠ Data

The package lives in `<repo-root>`. The data lives in `<dataset-root>`.
Updating one does not touch the other.

### Invariant 2 — Determinism

Two agents querying the same stable dataset produce the same answer.

### Invariant 3 — Auditability

Every fact carries `provenance.discovered_by`, `discovery_method`, and
`discovery_run` (when observed via SSH / Docker / etc.). If it can be
reproduced, it can be audited.

### Invariant 4 — Evidence separation

A fact (what) and the evidence for it (why) are stored separately. The
agent can reason on each independently.

### Invariant 5 — Stable identity, mutable observation

Endpoint `id`s are stable. The fields `host` / `port` / `protocol` describe
the observed access point and may change without altering the entity ID.
This lets an endpoint migrate from `192.168.1.50:3306` to
`192.168.1.54:3306` without breaking relations.

### Invariant 6 — Documentation Authority Hierarchy

When multiple documents describe the same surface and contradict,
authority is resolved by rank, not by majority:

```
1. cmdb/api.py:__all__                       ← normative (the surface itself)
2. docs/api-python.md                        ← canonical reference (derived)
3. README.md, integrations/hermes/SKILL.md   ← derived documentation
4. ~/.hermes/skills/knowledge-kernel/SKILL.md ← runtime artifact, never authoritative
```

**Default action when a discrepancy is found:** fix the documentation
to match `cmdb/api.py:__all__`. Touching code to accommodate docs
requires a real defect + breaking-change justification.

**Enforced by test:** `tests/test_doc_governance.py::test_skill_two_copies_remain_in_sync`
asserts the repo-side and runtime-side SKILL.md are byte-identical.
A red test is **evidence of an unresolved governance decision**, not
noise to suppress. Resolve the decision before relaxing the test.

Procedure when the test fails: backup the runtime copy first, classify
each diff block (correction / operational knowledge / error), then sync
in the appropriate direction. See
`references/public-api-audit-jul-2026.md` for the worked example
(commit `e0e9d64`, 2026-07-24).

---

## 6. Structure

```
SKILL.md              ← this file. Permanent + small.
docs/                 ← permanent reference
  philosophy.md        Why the Kernel exists (includes Repository/Instance Boundary)
  architecture.md      L1 + L2 engine
  observability.md     KAR / FGR / KHI
  governance.md        Inclusion test
  schema-v1.md         Entity YAML contract
  domain-model.md      Asset/Software/Endpoint/Evidence
  api-python.md        **Python API reference (canonical)**
  pitfalls/            One folder per pitfall
  playbooks/           Operational recipes
  history/             Experimental + historical
  releases/            User-facing release notes
references/           ← session-specific detail & operational guides
  repository-instance-boundary.md  Security sanitization + boundary principle
  skill-repo-sync.md               Skill ↔ repo sync workflow (critical)
  yaml-pitfalls.md                 YAML quoting and type gotchas
scripts/              ← maintenance tools
  update-github-meta.sh
```

---

## 7. Documentation & Positioning

### Project vs Category distinction

**knowledge-kernel** (lowercase, hyphenated) = this specific project/repository.

**Knowledge Kernel** (capitalized, spaces) = the architectural pattern/category that this project implements and aims to define.

Use the distinction consistently:
- Refer to the **project** as `knowledge-kernel` (code, repo, package name).
- Refer to the **concept** as "a Knowledge Kernel" or "the Knowledge Kernel pattern" when discussing the architectural category.

Section titles should speak to the **category**, not the brand:
- ✅ `## What a Knowledge Kernel Is Not`
- ✅ `## When to Use a Knowledge Kernel`
- ❌ `## What knowledge-kernel Is Not` (too narrow — speaks only to this repo)

This positioning reinforces that the project documents and exemplifies the pattern, not just implements it.

### Markdown format for "Use / Do not use" sections

When authoring "When to Use" or similar decision sections in documentation:

```markdown
## When to Use a Knowledge Kernel

Use knowledge-kernel when:

- ✓ Multiple agents need the same facts.
- ✓ Facts must be backed by evidence.
- ✓ Facts change over time and freshness matters.
- ✓ Deterministic retrieval is more important than semantic similarity.
- ✓ You need a shared source of truth across agents.

Do **not** use knowledge-kernel when:

- ✗ You need document retrieval → use a vector database.
- ✗ You need conversational memory → use an agent memory system.
- ✗ You need semantic similarity search → use embeddings.
- ✗ You need real-time monitoring → use Prometheus/Grafana.
```

Key formatting rules:
- Use proper markdown list bullets (`- ✓` / `- ✗`), not plain text with checkmarks.
- Emphasize negation: `Do **not** use` (not just "Do not use").
- End every list item with a period (`.`) for consistency.
- Use precise technical vocabulary: "semantic similarity search" (not "semantic search"), "agent memory system" (not "agent memory").
- Keep alternatives actionable: "→ use X" with a concrete tool/pattern.

### Branding migration workflow

For systematic project renaming across documentation, see:

**[`references/branding-migration-playbook.md`](references/branding-migration-playbook.md)** — Step-by-step workflow for rebranding initiatives, including triage heuristics (what to edit vs what to preserve), commit message templates, and verification steps.

---

### Compatibility vs Aesthetics — Decision Criterion

When considering whether to rename internal identifiers (env vars, default paths, module names, CLI commands), apply this test:

> **"Does this change bring value to the user, or only improve code aesthetics?"**

If only aesthetics → **postpone** until the next major version cycle (v2.0+).

**v1.x stability window:** Internal identifiers (`AGENT_CMDB_DATA_DIR`, `~/agent-cmdb/` defaults, `cmdb` module name, `cmdb` CLI) are intentionally preserved despite the public brand migration to "Knowledge Kernel". Breaking changes require:
- Bundled in a single v2.0 release
- Deprecation warnings for one full minor cycle
- Migration guide documenting the change
- Evidence of real-world adoption justifying the churn

See **[`references/runtime-compatibility-cleanup.md`](references/runtime-compatibility-cleanup.md)** for the full v2.0 roadmap and activation criteria.

---

## 8. Links

- [`docs/philosophy.md`](../knowledge-kernel/docs/philosophy.md) — Why build this?
- [`docs/architecture.md`](../knowledge-kernel/docs/architecture.md) — How the engine works
- [`docs/observability.md`](../knowledge-kernel/docs/observability.md) — Metrics framework
- [`docs/governance.md`](../knowledge-kernel/docs/governance.md) — Inclusion criteria
- [`docs/schema-v1.md`](../knowledge-kernel/docs/schema-v1.md) — Entity schema
- [`docs/domain-model.md`](../knowledge-kernel/docs/domain-model.md) — Asset/Software/Endpoint/Evidence
- [`docs/api-python.md`](../knowledge-kernel/docs/api-python.md) — **Python API reference (canonical)**
- [`docs/pitfalls/`](../knowledge-kernel/docs/pitfalls/) — One file per pitfall
- [`docs/playbooks/`](../knowledge-kernel/docs/playbooks/) — Operational recipes
- [`docs/history/`](../knowledge-kernel/docs/history/) — Experimental + historical
- [`docs/releases/`](../knowledge-kernel/docs/releases/) — Release notes
- [`references/inspector-pattern.md`](references/inspector-pattern.md) — Inspector pattern: falsable,
  deterministic findings; companion to `public-api-audit-jul-2026.md`
- [`references/pi-01-operational-knowledge.md`](references/pi-01-operational-knowledge.md) — Research
  programme PI-01: deciding when operational knowledge deserves a component