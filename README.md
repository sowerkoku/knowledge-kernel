# Agent-CMDB

**A deterministic factual substrate for AI agents.**

```
Facts · Evidence · Freshness · Deterministic API
```

> "It does not reason, infer, or decide."

---

## 1. The Problem

LLMs have a fundamental flaw: they **mix facts with reasoning**.

When an LLM responds to "Where does Ollama run?" it:
- Infers from training data (often wrong)
- Does not share a single source of truth with other agents
- Cannot verify whether its answer is current

**Agent-CMDB exists to fix this.**

It provides a shared, verified factual substrate so agents can:
- Query **what exists** before making claims
- Verify **where things are** before acting on them
- Analyze **what breaks** before making changes
- Track **when facts become stale**

---

## 2. What is the Knowledge Kernel?

```
Knowledge Kernel
       │
       ▼
Verified Facts (from the Kernel)
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

The Kernel is **not** a database. It is a contract:

> *"If a fact is not in the Kernel, the agent treats it as unverified."*

Only three things live in the Kernel:
- **Entity** — What exists
- **Evidence** — Why we trust it
- **Freshness** — When it was observed and when it expires

Reasoning and decisions live **outside** — in the LLM.

---

## 3. Core Principles

**1. The API is the product.**
Code and dataset will change. The public API (`cmdb.api`) must not break without strong architectural reason. Stability enables independent evolution of consumers.

**2. The Kernel stays small.**
It answers: *"Does this fact exist?"* and *"What depends on it?"*
It does not store documentation, conversations, or inferred knowledge.

**3. Metrics govern evolution.**
Change the Kernel when evidence demands it — not anticipation.
Example: *"Fact Coverage is low in infrastructure"* → expand infrastructure.

**4. Facts ≠ Evidence ≠ Reasoning.**
- **Facts** — What exists (schema-validated)
- **Evidence** — Why we trust it (source, confidence, observed_at)
- **Reasoning** — What the LLM decides (outside the Kernel)

**5. Freshness is computed, never stored.**
The Kernel records `observed_at`. It derives freshness at query time from domain TTLs.

**6. Every assertion requires evidence.**
If a fact is not backed by the Kernel, the agent must say so.

---

## 4. Domain Model

```
┌─────────────────────────────────────────┐
│               Asset                      │
│    Where software runs (physical host)  │
│    Example: orange-pi-54                 │
└─────────────────────────────────────────┘
                    ▲
                    │ runs_on
                    │
┌─────────────────────────────────────────┐
│              Software                    │
│    What executes (process or service)    │
│    Example: ollama, mysql, metabase      │
└─────────────────────────────────────────┘
                    │
                    │ exposes
                    ▼
┌─────────────────────────────────────────┐
│              Endpoint                    │
│    Observable communication identity     │
│    ID = stable, host/port/protocol may  │
│    change without changing the ID        │
│    Example: ollama-api (192.168.1.54:   │
│    11434, http)                          │
└─────────────────────────────────────────┘
                    │
                    │ exposed_by
                    ▼
              Evidence (source, confidence,
              observed_at, expires_at)
```

**Entity responsibilities — each answers one question:**

| Entity | Question it answers |
|--------|-------------------|
| `Asset` | Where does it run? |
| `Software` | What executes? |
| `Endpoint` | How can other components communicate with it? |
| `Evidence` | Why do we believe this is true? |

---

## 5. Public API

Only eight functions — all in `cmdb.api`:

```python
from cmdb.api import (
    cmdb_exists,    # Check before making any factual claim
    cmdb_get,       # Entity + evidence (includes entity.runs_on property)
    cmdb_list,      # Filter by kind / domain / status
    cmdb_search,    # Find by name / description / tags
    cmdb_impact,    # Dependency graph — what breaks if X changes/fails?
    cmdb_assert,    # Binary validation for decisions
    cmdb_context,   # Pre-packaged agent startup context
    cmdb_validate,  # CMDB health check
)
```

Everything else in the `cmdb` package is internal — subject to change.

---

## 6. Complete Example

**Question:** "Where does Ollama run?"

```
User
  │
  ▼
cmdb_get("ollama")
  │
  ▼
entity.id      = "ollama"
entity.kind    = "software"
entity.runs_on = "orange-pi-54"   ← computed property
entity.relations = [{type: "runs_on", target: "orange-pi-54"},
                   {type: "exposes", target: "ollama-api"}]
evidence.confidence_level = HIGH
evidence.confidence_basis = [SCHEMA_VALIDATED, HUMAN_DECLARED]
  │
  ▼
LLM Reasoning
  │
  ▼
Answer: "Ollama runs on orange-pi-54"
```

**Question:** "What happens if port 11434 fails?"

```
cmdb_impact("ollama-api")
  │
  ▼
ollama-api (the endpoint)
  │
  ▼
depends_on_me.direct: [{id: "ollama", kind: "software", relation: "exposes"}]
ollama depends_on_me.direct: [{id: "open-webui", kind: "software", relation: "uses"}]
risk_indicators.single_point_of_failure: True
  │
  ▼
Answer: "Closing port 11434 removes Ollama → OpenWebUI loses its LLM backend"
```

---

## 7. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Repository                             │
│                    ~/agent-cmdb/                              │
│  Code (pip-installable) — versioned in git                    │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼ pip install -e
┌──────────────────────────────────────────────────────────────┐
│                    Hermes Skill                               │
│               ~/.hermes/skills/agent-cmdb/                    │
│  SKILL.md = contract between Hermes and the Kernel             │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   Knowledge Dataset                           │
│              ~/knowledge/agent-cmdb/                          │
│  YAML entities (Asset / Software / Endpoint / etc.)           │
│  Code ≠ Data — updating the package never touches this         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                       Agents                                  │
│              Hermes, Codex, Claude Code, etc.                │
│  They query facts, not memory                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. What Agent-CMDB Is NOT

| Not | Because |
|-----|---------|
| IT inventory | Not for human browsing; for agent grounding |
| Monitoring | No real-time metrics |
| Automation | Does not execute actions |
| LLM memory | No conversational history |
| Knowledge base | No documentation or narratives |
| CMDB classic | Not NetBox or ServiceNow — it is a deterministic factual substrate |

---

## 9. Quick Start

```bash
# Clone
git clone https://github.com/sowerkoku/agent-cmdb.git
cd agent-cmdb

# Install (use Hermes venv, not system Python)
~/.hermes/hermes-agent/venv/bin/python3 -m pip install -e .

# Configure
export CMDB_DATA_DIR=~/knowledge/agent-cmdb

# Verify
python3 -c "from cmdb.api import cmdb_get; print(cmdb_get('ollama').entity.runs_on)"
# → orange-pi-54
```

---

## 10. Roadmap

| Version | Focus |
|---------|-------|
| **v1.0** | Core API, Asset/Software/Endpoint model, evidence tracking |
| **v1.1** | Lazy integration with Hermes agents |
| **v1.2** | Endpoint model, exposes/exposed_by, computed `entity.runs_on` |
| **Future** | Runtime Discovery skill (SSH → evidence → proposal → human approval) |

---

## License

MIT — Carlos Cáceres, 2026