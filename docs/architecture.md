---
title: Architecture — Agent-CMDB
---

# Architecture

**Purpose:** Explain *how* the parts fit together.
For *why* the parts exist → see [`philosophy.md`](./philosophy.md).

---

## 1. The Pipeline

```
Knowledge Kernel
       │
       ▼
Verified Facts
       │
       ▼
  LLM Reasoning
       │
       ▼
   Decision
       │
       ▼
    Action
```

The Kernel produces verifiable inputs. Reasoning happens in the LLM. Decisions happen in the user. Actions trigger tool execution.

---

## 2. Repository Architecture

```
┌───────────────────────────────────────────────────────────────┐
│  Repository  ~/agent-cmdb/                                    │
│  pip-installable Python package, versioned in git             │
│                                                               │
│  Files:                                                       │
│    cmdb/api.py          ← 8 public functions                 │
│    cmdb/query.py        ← core read API                      │
│    cmdb/impact.py       ← dependency graph engine              │
│    cmdb/models/         ← Entity / Evidence / Result objects  │
│    cmdb/validator.py    ← schema + integrity check            │
│    cmdb/audit.py        ← coverage + freshness report         │
│    cmdb/taxonomy.py     ← kind / domain catalog               │
│    cmdb/assertions.py   ← cmdb_assert() logic                 │
│    cmdb/config.py       ← CMDB_DATA_DIR, env vars              │
└───────────────────────────────────────────────────────────────┘
                            │
                            ▼ pip install -e
┌───────────────────────────────────────────────────────────────┐
│  Hermes Skill  ~/.hermes/skills/agent-cmdb/                   │
│                                                               │
│  SKILL.md = contract between Hermes and the Kernel            │
│    - 8 functions, complete signatures                         │
│    - API behavior with examples                               │
│    - Domain model summary                                     │
└───────────────────────────────────────────────────────────────┘
                            │
                            ▼ CMDB_DATA_DIR (env var)
┌───────────────────────────────────────────────────────────────┐
│  Knowledge Dataset     ~/knowledge/agent-cmdb/                │
│  Production YAML entities                                     │
│                                                               │
│    asset/             ← hardware (orange-pi-54, servidor-pos) │
│    software/          ← services (ollama, mysql, hermes)      │
│    endpoint/          ← communication identities              │
│    automation/        ← sync pipelines, scheduled jobs        │
│    data/              ← databases, backups                    │
└───────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  Agents (Hermes, Codex, ...)                                  │
│  They query facts; they do not invent them.                   │
└───────────────────────────────────────────────────────────────┘
```

### Code ≠ Data — permanently separated

| Layer | Mutable? | Versioned? |
|-------|----------|------------|
| `~/agent-cmdb/` (code) | Reinstallable | Yes — git |
| `~/.hermes/skills/agent-cmdb/` (skill) | Editable locally | No |
| `~/knowledge/agent-cmdb/` (dataset) | Editable, auditable | Yes — git (separate repo) |

**Rule:** Updating the package never touches the dataset. Updating the dataset never requires package reinstall.

---

## 3. Domain Model in Code

```
ASSET (orange-pi-54)
    ↑
    │ runs_on         ← 1-hop lookup
    │
SOFTWARE (ollama)
    │
    │ exposes         ← 1-hop lookup
    ▼
ENDPOINT (ollama-api)
    │
    ▲ exposed_by      ← inverse of exposes
    │
    │
    ▲ used_by         ← inverse of uses
SOFTWARE (open-webui)
    │
    │ uses
    ▼
SOFTWARE (ollama)
```

Each arrow is a typed relation with a defined target constraint:

| Arrow | Constraint |
|-------|------------|
| `runs_on` | Always `kind: asset`. Invariant: at most one per software. |
| `exposes` | Always `kind: endpoint`. Software may expose multiple endpoints. |
| `uses` | Any kind (except `asset`). |
| `reads` / `writes` | `kind: data` or `kind: software`. |
| `calls` | `kind: endpoint` or `kind: software`. |

---

## 4. cmdb_impact() Internals

The Kernel resolves dependencies in two directions:

```python
# Forward: what does X depend on?
depends_on = traverse_relations(X, direction="outbound")

# Reverse: what depends on X?
depends_on_me = traverse_relations(X, direction="inbound")
```

To answer *"what breaks if port 11434 fails?"*:

```
cmdb_impact("ollama-api")
   │
   ▼ (inbound, exposed_by)
   → ollama
   │
   ▼ (inbound, uses)
   → open-webui
   │
   ▼ (inbound, uses)
   → ...  (BFS until cycle or visited)
```

`depends_on_me` includes:
- `direct`: entities one hop away
- `transitive`: entities reachable through any chain

**Risk indicators** derived from the graph:

| Indicator | Meaning |
|-----------|---------|
| `single_point_of_failure` (SPOF) | No redundant alternative |
| `critical_dependents` | Dependents with `business: high` |
| `depends_chain_depth` | Longest transitive chain |

---

## 5. Evidence and Freshness

```yaml
evidence:
  source_file: software/ollama.yaml
  confidence_level: HIGH
  confidence_basis: [SCHEMA_VALIDATED, HUMAN_DECLARED]
  observed_at: "2026-07-07T00:00:00Z"
```

Domains have TTLs:

| Domain | Default TTL | Effect |
|--------|-------------|--------|
| infrastructure | 1 hour | Re-verify quickly |
| endpoints | 5–15 minutes | Connection details change often |
| software | 24 hours | Service identity stable |
| policies | 30 days | Change rarely |
| procedures | 90 days | Runbooks rarely move |

`expires_at = observed_at + domain TTL`. Computed at query time, never stored.

---

## 6. Iteration Plan

```
v1.0 (2026-07-06)  →  Core API, evidence, freshness      [SHIPPED]
v1.2 (2026-07-07)  →  Endpoint model, exposes/exposed_by [SHIPPED]
v1.3                →  Lazy integration with Hermes
                       (cmdb_context() called per query, not at startup)
Future              →  Runtime Discovery skill
                       (SSH/ss/Docker probe → Evidence → Proposal)
```

---

## References

- [`philosophy.md`](./philosophy.md) — Why the Kernel exists
- [`domain-model.md`](./domain-model.md) — Entity responsibilities
- [`schema-v1.md`](./schema-v1.md) — YAML specification