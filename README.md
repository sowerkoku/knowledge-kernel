# Agent-CMDB

**A deterministic factual substrate for AI agents.**

- **Facts** — verified entities, not inferred knowledge
- **Evidence** — why we trust each fact
- **Freshness** — when it was observed, when it expires
- **Deterministic API** — same data, same time, same result

---

## The Problem

LLMs mix facts with reasoning. When an LLM answers "Where does Ollama run?" it:
- Infers from training data — often wrong
- Cannot verify whether its answer is current
- Does not share a single source of truth with other agents

**Agents need a shared factual substrate they can query, not a model that guesses.**

---

## What is the Knowledge Kernel?

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

The Kernel is not a database. It is a contract:

> *If a fact is not in the Kernel, the agent treats it as unverified.*

Only three things live here: **what exists**, **why we trust it**, and **when it was observed**. Reasoning and decisions live in the LLM — not in the Kernel.

---

## Six Principles

**1. The API is the product.**
The dataset will change. The implementation will change. The public API must not break without a strong architectural reason. Stability enables independent evolution of all consumers.

**2. The Kernel stays small.**
It answers: *"Does this fact exist?"* and *"What depends on it?"*
It does not store documentation, conversations, or inferred knowledge. That belongs to other systems.

**3. Metrics govern evolution.**
Expand the Kernel when evidence demands it — not anticipation.
Good: *"Fact Coverage is low in infrastructure."*
Bad: *"We could add 50 more entities."*

**4. Facts ≠ Evidence ≠ Reasoning.**
- **Facts** — what exists (schema-validated)
- **Evidence** — why we trust it (source, confidence, observed_at)
- **Reasoning** — what the LLM decides (outside the Kernel)

**5. Freshness is computed, never stored.**
The Kernel records `observed_at`. It derives freshness at query time from domain TTLs. No stale values.

**6. Every assertion requires evidence.**
If a fact is not backed by the Kernel, the agent must say so — not infer.

---

## Domain Model

```
┌─────────────────────────────────────────┐
│                 Asset                    │
│    Where software runs                   │
│    Example: orange-pi-54                 │
└─────────────────────────────────────────┘
                    ▲
                    │ runs_on
                    │
┌─────────────────────────────────────────┐
│               Software                   │
│    What executes                         │
│    Example: ollama, mysql                │
└─────────────────────────────────────────┘
                    │
                    │ exposes
                    ▼
┌─────────────────────────────────────────┐
│               Endpoint                   │
│    Observable communication identity     │
│                                         │
│  ID = stable (ollama-api)               │
│  host/port/protocol = observed facts    │
│  (may change without changing the ID)  │
└─────────────────────────────────────────┘
                    │
                    │ exposed_by
                    ▼
              Evidence
```

Each entity answers one question:

| Entity | Question |
|--------|----------|
| `Asset` | Where does it run? |
| `Software` | What executes? |
| `Endpoint` | How can other components communicate with it? |
| `Evidence` | Why do we believe this is true? |

---

## Public API

Eight functions. Nothing else is public.

```python
from cmdb.api import (
    cmdb_exists,    # Check before making any factual claim
    cmdb_get,       # Entity + evidence (+ entity.runs_on computed property)
    cmdb_list,      # Filter by kind / domain / status
    cmdb_search,    # Find by name / description / tags
    cmdb_impact,    # What breaks if X changes? (dependency graph)
    cmdb_assert,    # Binary validation for decisions
    cmdb_context,   # Pre-packaged agent startup context (lazy)
    cmdb_validate,  # CMDB health check
)
```

Everything else in the `cmdb` package is internal — subject to change.

---

## Complete Flow

**User:** "Where does Ollama run?"

```
cmdb_get("ollama")
  │
  ▼
entity.id         = "ollama"
entity.kind       = "software"
entity.runs_on    = "orange-pi-54"          ← computed property
entity.relations  = [{type: "runs_on", target: "orange-pi-54"},
                    {type: "exposes", target: "ollama-api"}]
evidence.confidence_level = HIGH
evidence.confidence_basis = [SCHEMA_VALIDATED, HUMAN_DECLARED]
  │
  ▼
LLM Reasoning
  │
  ▼
"Ollama runs on orange-pi-54"
```

**User:** "What happens if port 11434 fails?"

```
cmdb_impact("ollama-api")
  │
  ▼
ollama-api
  │
  ▼
depends_on_me.direct:     [{id: "ollama",    kind: "software", relation: "exposes"}]
ollama.depends_on_me.direct: [{id: "open-webui", kind: "software", relation: "uses"}]
SPOF: True
  │
  ▼
"Closing port 11434 removes Ollama → OpenWebUI loses its LLM backend"
```

---

## Architecture

```
Repository (~/agent-cmdb/)      ← pip-installable code, versioned in git
         │
         ▼ pip install -e
Hermes Skill (agent-cmdb/)      ← SKILL.md = contract between agent and Kernel
         │
         ▼ CMDB_DATA_DIR
Knowledge Dataset               ← YAML entities: Asset / Software / Endpoint
         │
         ▼
Agents (Hermes, Codex, ...)     ← they query facts, not memory
```

Code and data are permanently separated. Updating the package never touches the dataset.

---

## Philosophy

> *"It does not reason, infer, or decide."*

This is the identity of the Kernel. It is not a smart system. It is a trustworthy one. The Kernel provides inputs so agents can reason — it does not reason for them.

---

## What Agent-CMDB Is NOT

| Not | Because |
|-----|---------|
| IT inventory | Not for human browsing; for agent grounding |
| Monitoring | No real-time metrics |
| Automation | Does not execute actions |
| LLM memory | No conversational history |
| Knowledge base | No documentation or narratives |
| A CMDB | Not NetBox or ServiceNow — it is a deterministic factual substrate |

---

## Roadmap

```
v1.2  →  Endpoint model, exposes/exposed_by, computed entity.runs_on
v1.1  →  Lazy integration with Hermes agents
Future →  Runtime Discovery skill (SSH → evidence → proposal → human approval)
```

---

## Quick Start

```bash
git clone https://github.com/sowerkoku/agent-cmdb.git
cd agent-cmdb

# Use Hermes venv, not system Python
~/.hermes/hermes-agent/venv/bin/python3 -m pip install -e .

export CMDB_DATA_DIR=~/knowledge/agent-cmdb

# Verify
python3 -c "from cmdb.api import cmdb_get; print(cmdb_get('ollama').entity.runs_on)"
# → orange-pi-54
```

---

## License

MIT — Carlos Cáceres, 2026