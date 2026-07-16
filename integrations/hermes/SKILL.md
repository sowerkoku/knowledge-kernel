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

**Decide a question with grounding:**

> 1. Does the Kernel have it? Query it.
> 2. Does the Kernel have the path to observe it? Query the path, then observe.
> 3. Otherwise: say "I don't have grounds to answer."

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

```python
from cmdb.api import (
    cmdb_exists,    # Existence check before any factual claim
    cmdb_get,       # Full entity with evidence + relations
    cmdb_search,    # Free-text search by name/desc/tags
    cmdb_list,      # Filter by kind/domain/status
    cmdb_context,   # Pre-packaged agent context (call once at start)
    cmdb_impact,    # Dependency graph (BEFORE modifying anything)
    cmdb_assert,    # Binary assertion for decision points
    cmdb_validate,  # Health check on the whole Kernel
)
```

Everything else inside `cmdb/` is **internal** and may change without notice.

> **API Reference**: The canonical, complete documentation of the public
> API (all functions, return types, usage patterns, best practices,
> anti-patterns, compatibility) lives in
> [`docs/api-python.md`](../knowledge-kernel/docs/api-python.md).
>
> This skill only lists the entry points. For signatures, examples,
> and return-type details, read the canonical reference.

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

---

## 4. Contract — what must never break?

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

---

## 5. Structure

```
SKILL.md              ← this file. Permanent + small.
docs/                 ← permanent reference
  philosophy.md        Why the Kernel exists
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
```

---

## 6. Links

- [`docs/philosophy.md`](../knowledge-kernel/docs/philosophy.md) — Why build this?
- [`docs/architecture.md`](../knowledge-kernel/docs/architecture.md) — How the engine works
- [`docs/observability.md`](../knowledge-kernel/docs/observability.md) — Metrics framework
- [`docs/governance.md`](../knowledge-kernel/docs/governance.md) — Inclusion criteria
- [`docs/schema-v1.md`](../knowledge-kernel/docs/schema-v1.md) — Entity schema
- [`docs/domain-model.md`](../knowledge-kernel/docs/domain-model.md) — Asset/Software/Endpoint/Evidence
- **`docs/api-python.md`** — **Python API reference (canonical)**
- [`docs/pitfalls/`](../knowledge-kernel/docs/pitfalls/) — One file per pitfall
- [`docs/playbooks/`](../knowledge-kernel/docs/playbooks/) — Operational recipes
- [`docs/history/`](../knowledge-kernel/docs/history/) — Experimental + historical
- [`docs/releases/`](../knowledge-kernel/docs/releases/) — Release notes