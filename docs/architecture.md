# Architecture — knowledge-kernel Knowledge Kernel

**How do the pieces connect? Where does everything live?**

This document is the single source of truth for the system's architecture. All other documents reference it.

---

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      Repository                               │
│                  ~/agent-cmdb/                               │
│                                                              │
│  Code (pip-installable) — versioned in git                   │
│  ├── cmdb/api.py         ← public API (8 functions)          │
│  ├── cmdb/models/        ← Entity, Evidence, CMDBResult      │
│  ├── cmdb/query.py       ← cmdb_get, cmdb_list, cmdb_search  │
│  ├── cmdb/impact.py      ← dependency graph, risk indicators │
│  └── tests/              ← Core tests (14/14 ✅)             │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ pip install -e
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    Hermes Skill                              │
│             ~/.hermes/skills/agent-cmdb/                     │
│                                                              │
│  SKILL.md = contract between Hermes and the Kernel           │
│  This is what Hermes loads — it defines the interface        │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ CMDB_DATA_DIR env var
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   Knowledge Dataset                           │
│              ~/knowledge/agent-cmdb/                          │
│                                                              │
│  YAML entities — code and data are permanently separated     │
│  ├── software/         ← kind: software                      │
│  ├── asset/           ← kind: asset                          │
│  ├── endpoint/        ← kind: endpoint                       │
│  ├── automation/      ← kind: automation                     │
│  └── data/           ← kind: data                           │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ cmdb.api functions
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                       Agents                                  │
│         Hermes, Codex, Claude Code, other AI agents         │
│                                                              │
│  They query facts — not memory, not inference                │
└──────────────────────────────────────────────────────────────┘
```

**Key property:** Updating the package (`pip install -e`) never touches the dataset. The dataset is independent.

---

## 2. Code vs Data Separation

| Component | Location | Managed by |
|-----------|----------|-----------|
| **Code** | `~/agent-cmdb/` | `pip install -e .` — versioned in git |
| **Skill** | `~/.hermes/skills/agent-cmdb/` | Hermes curator |
| **Dataset** | `~/knowledge/agent-cmdb/` | Runtime Discovery + human approval |

The Kernel is **not** the dataset. The Kernel is the code that interprets the dataset.

---

## 3. The Deterministic Pipeline

Every interaction follows this pipeline:

```
┌──────────────────────────────────────────────────────────────────┐
│                        User Question                              │
│                  "Where does Ollama run?"                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                         Need Facts?                               │
│                  Decision: cmdb_get("ollama")                    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Knowledge Kernel                              │
│                                                                 │
│  Query: entity = cmdb_get("ollama")                             │
│  Response: Entity(id="ollama", kind="software",                 │
│                   runs_on="orange-pi-54",                       │
│                   relations=[...])                               │
│  Evidence: confidence_level=HIGH, confidence_basis=[...],       │
│             observed_at=2026-07-07T...                           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      LLM Reasoning                                │
│                                                                 │
│  "The Kernel says Ollama runs on orange-pi-54."                 │
│  "This is verified: schema_validated + human_declared."        │
│  "Confidence: HIGH."                                            │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Grounded Answer                             │
│                                                                 │
│  "Ollama runs on orange-pi-54 (verified, HIGH confidence)."     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Impact Analysis Pipeline

For questions like *"What breaks if X fails?"*:

```
┌──────────────────────────────────────────────────────────────────┐
│                    cmdb_impact("ollama-api")                     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Dependency Graph                               │
│                                                                 │
│  ollama-api                                                     │
│      │                                                          │
│      │ exposed_by (1-hop, NOT transitive)                       │
│      ▼                                                          │
│  ollama                                                         │
│      │                                                          │
│      │ uses (transitive)                                        │
│      ▼                                                          │
│  open-webui                                                     │
│      │                                                          │
│      │ uses (transitive)                                        │
│      ▼                                                          │
│  hermes-webon                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Risk Indicators                                 │
│                                                                 │
│  single_point_of_failure: True                                  │
│  critical_dependents: [open-webui, hermes-webon]                │
│  cascade_depth: 2                                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. The Lazy Integration Contract

Hermes loads the skill at startup, but **does not call the Kernel**. The Kernel is consulted only when:

1. The agent needs to answer a question about infrastructure reality
2. Before making any factual assertion
3. Before modifying anything (impact analysis)

```
hermes startup:    SKILL.md loaded, cmdb.api imported
                          ↓
                    NO Kernel calls
                          ↓
user question:     "Can I restart Ollama?"
                          ↓
                    cmdb_get("ollama") + cmdb_impact("ollama")
                          ↓
                    Kernel response
                          ↓
                    LLM Reasoning
                          ↓
                    "Yes — but open-webui depends on it. SPOF."
```

---

## 6. Package Structure

```
~/agent-cmdb/
├── README.md              ← project entry point
├── cmdb/
│   ├── __init__.py        ← package init
│   ├── api.py             ← 8 public functions (THE ONLY PUBLIC API)
│   ├── config.py          ← CMDB_DATA_DIR + environment
│   ├── query.py           ← cmdb_get, cmdb_list, cmdb_search (internal loader)
│   ├── impact.py          ← dependency graph + risk indicators
│   ├── validator.py       ← YAML schema validation
│   ├── assertions.py      ← binary assertions (cmdb_assert)
│   ├── audit.py           ← cmdb_validate (health check)
│   └── models/
│       ├── __init__.py
│       ├── entity.py      ← Entity dataclass + entity.runs_on property
│       └── result.py      ← CMDBResult, Evidence dataclasses
├── tests/
│   └── test_acceptance.py ← 14 Core Tests ✅
├── docs/
│   ├── philosophy.md      ← principles + KPIs (THIS FILE)
│   ├── architecture.md    ← THIS FILE
│   ├── domain-model.md    ← entity responsibilities
│   ├── schema-v1.md       ← YAML specification
│   ├── usage-patterns.md  ← query patterns
│   ├── governance.md      ← what enters the Kernel
│   ├── audit-methodology.md ← how to audit
│   ├── error-log.md       ← failure modes
│   └── github-metadata.md ← repo metadata
└── migration/
    └── migration-plan.md  ← 72 entities, 71 relations preserved
```

---

## 7. Where `cmdb.api` Lives

The public API is exclusively in `cmdb.api`:

```python
from cmdb.api import (
    cmdb_exists,    # → {exists: bool, confidence: str}
    cmdb_get,       # → CMDBResult(entity, evidence)
    cmdb_list,      # → list[dict] (no CMDBResult wrapper)
    cmdb_search,    # → list[dict]
    cmdb_impact,    # → {exists, dependency_graph, risk_indicators}
    cmdb_assert,    # → bool (binary validation)
    cmdb_context,   # → dict (agent startup context)
    cmdb_validate,  # → {valid, stats, errors, warnings}
)
```

Everything else in `cmdb/` is internal. It can change between versions without notice.

---

## See also

- [`README.md`](../README.md) — Project overview and quick start
- [`philosophy.md`](./philosophy.md) — Design principles and KPIs (unique source: six principles, FGR/Coverage/Freshness)
- [`domain-model.md`](./domain-model.md) — Entity responsibilities (Asset / Software / Endpoint / Evidence)
- [`schema-v1.md`](./schema-v1.md) — YAML serialization format