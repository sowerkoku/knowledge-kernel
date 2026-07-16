# knowledge-kernel

**A governed, deterministic and reproducible factual substrate for AI agents.**

---

## 🧊 L2.1 Status: Production Ready

```
BUILD MODE   = OFF
OBSERVE MODE = ON
```

The next architecture must emerge from **observed usage patterns and empirical evidence**, not anticipation.

**Permitted:**
- Run Hermes normally
- Expand dataset (empirical learning, not architectural change)
- Fix bugs (defects only)
- Improve documentation
- Performance tuning that preserves public contracts and architectural boundaries
- Analysis of telemetry across the 5 primary indicators

**Not permitted:**
- New APIs
- New indexes not triggered by observed patterns
- New engines or layers
- Proposal queues
- Evidence engines
- Auto-reload / file watchers
- Architectural redesign

### Stated configuration

```
Architecture:        Frozen
Dataset:             Evolvable
Telemetry:           Active
Decision-making:     Evidence-driven
Minimum observation: 100 real queries
```

### Maturity (per area)

| Area | Status | Notes |
|------|--------|-------|
| Factual model | High maturity | L2 stable |
| Determinism | High maturity | L2 stable |
| Observability | Good | L2.1 complete |
| Governance | Good | OBSERVE RULE 1 + 5 indicators |
| Multi-writer | Consciously deferred | Not yet needed |
| Factual evolution | Sufficient | Empirically guided |
| Empirical evidence | Pending | Awaiting 100–500 queries |

### Closing milestone statement

> The architecture is stable enough to stop designing
> and mature enough to start learning from reality.

The next valuable information is **not** in additional architecture.
It is in the behavior Hermes produces across real queries. Bugs,
documentation gaps, and dataset coverage needs are all expected and
*permitted* under OBSERVE RULE 1. What is **frozen** is the
architecture, not the project.

### Operational motto

```
Observe first.
Conclude second.
Design last.
```

Or equivalently:

```
Reality
   ↓
Evidence
   ↓
Conclusion
   ↓
Architecture
```

### The emergent contract

```
Canonical YAML
   ↓
Deterministic Indexes
   ↓
Stable Public API
   ↓
Telemetry
   ↓
Empirical Learning
```

---

knowledge-kernel manages evidence-backed claims about reality, their provenance, relationships and recency, so that multiple agents can reason from the same auditable view of the world.

It is not a memory system, a vector store, or a RAG corpus. It is governed epistemic infrastructure — a system that defines what can be considered a shared and defensible fact for agents.

knowledge-kernel is a **deterministic, reproducible and auditable factual substrate** for AI agents.

It stores verified facts, the evidence supporting them, their relationships and their recency, so that multiple agents can reason from the same observable reality.

- **Determinism** — Two agents with the same Kernel state obtain the same factual answer.
- **Auditability** — Every fact answers: What do we know? Why do we believe it? When was it observed? How was it discovered? Who incorporated it?
- **Reproducibility** — Given the same `dataset_hash` and the same query, agents obtain the same factual answer.

### The Four Layers

```
Reality
   ↓
Observations / Evidence   ← source + observed_at + discovery_method
   ↓
Structured Facts (Entities + Relations)
   ↓
Grounded Reasoning         ← Agents query the Kernel, then reason deterministically
```

> Evidence is epistemically primary. Entities are merely the serialization of accepted facts.

### `dataset_hash` in three invariants

Reproduction, audit, and identity rest on three guarantees. They are
explicit, not implicit:

| Invariant | Stated rule |
|-----------|-------------|
| **Stability** | Same dataset ⇒ same `dataset_hash` |
| **Sensitivity** | Different dataset contents ⇒ different `dataset_hash` |
| **Independence** | Same `dataset_hash` ⇏ same `engine_generation` (factual identity ≠ runtime state) |

The hash represents **factual identity**, not operational state. It is
content-addressed, which is exactly what makes reproducibility a
contract — not a marketing claim.

---

## The Problem

**LLMs infer. Facts drift. Agents disagree. Evidence disappears.**

When an LLM answers "Where does Ollama run?" it:
- Infers from training data — often wrong
- Cannot verify whether its answer is current
- Does not share a single source of truth with other agents
- Loses the trail of *what* was known, *why* it was trusted, *when* it was observed, and *how* it was discovered

Agents need a shared deterministic factual layer they can query — one that preserves *what*, *why*, *when*, and *how* — not a model that guesses.

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

## Why Not RAG?

| RAG | knowledge-kernel |
|-----|-----------|
| Similarity search | Deterministic lookup |
| Documents | Facts |
| Probabilistic retrieval | Exact retrieval |
| Chunk embeddings | Structured entities |
| Agent-specific context | Shared factual substrate |

RAG finds *similar documents*. knowledge-kernel answers *what exists and what depends on it*.

---

## Why Not Agent Memory?

| Agent Memory | knowledge-kernel |
|--------------|-----------|
| Experiences | Facts |
| Conversations | Verified knowledge |
| Subjective | Objective |
| Personal | Shared across agents |
| Mutable | Evidence-backed |

Memory stores *what happened*. The Kernel stores *what is true*.

---

## Domain Model

```
┌─────────────────────────────────────────┐
│                 Asset                    │
│    Where software runs                   │
│    Example: app-server-01                 │
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

The public API is intentionally small.
**New APIs require empirical evidence gathered during OBSERVE MODE.**

```python
from cmdb.api import (
    cmdb_exists,    # Check before making any factual claim
    cmdb_get,       # Entity + evidence (+ entity.runs_on computed property)
    cmdb_list,      # Filter by kind / domain / status
    cmdb_search,    # Find by name / description / tags
    cmdb_impact,    # What breaks if X changes? (dependency graph)
    cmdb_assert,    # Binary validation for decisions
    cmdb_context,   # Pre-packaged agent startup context (lazy)
    cmdb_validate,  # Dataset / schema validation
)
```

Operational introspection (not in public API, available via skill tools):
- `cmdb_reload()` — explicit index invalidation + observable contract
- `cmdb_engine_info()` — runtime metadata (generation, dataset_hash, index counts)
- `cmdb_stats()` — dataset summary (entity counts by kind)

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
entity.runs_on    = "app-server-01"          ← computed property
entity.relations  = [{type: "runs_on", target: "app-server-01"},
                    {type: "exposes", target: "ollama-api"}]
evidence.confidence_level = HIGH
evidence.confidence_basis = [SCHEMA_VALIDATED, HUMAN_DECLARED]
  │
  ▼
LLM Reasoning
  │
  ▼
"Ollama runs on app-server-01 (verified, HIGH confidence)"
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

## Six Principles

**1. The API is the product.**
The dataset will change. The implementation will change. The public API must not break without a strong architectural reason.

**2. The Kernel stays small.**
It answers: *"Does this fact exist?"* and *"What depends on it?"* — nothing more.

**3. Metrics govern evolution.**
Expand when evidence demands it — not anticipation. Example: *"Fact Coverage is low in infrastructure"* → expand infrastructure.

**4. Facts ≠ Evidence ≠ Reasoning.**
- **Facts** — what exists (schema-validated)
- **Evidence** — why we trust it (source, confidence, observed_at)
- **Reasoning** — what the LLM decides (outside the Kernel)

**5. Freshness is computed, never stored.**
The Kernel records `observed_at`. It derives freshness at query time from domain TTLs. No stale values.

**6. Every assertion requires evidence.**
If a fact is not in the Kernel, the agent must say so — not infer.

---

## Architecture

```
Repository (~/knowledge-kernel/)      ← pip-installable code, versioned in git
         │
         ▼ pip install -e
Hermes Skill (knowledge-kernel)      ← SKILL.md = contract between agent and Kernel
         │
         ▼ CMDB_DATA_DIR
Knowledge Dataset               ← YAML entities: Asset / Software / Endpoint
         │
         ▼
Agents (Hermes, Codex, ...)     ← they query facts, not memory
```

Code and data are permanently separated. Updating the package never touches the dataset.

---

## What a Knowledge Kernel Is NOT

| Not | Because |
|-----|---------|
| RAG / Vector DB | Does not search similar documents — answers exact factual questions |
| Agent Memory | Does not store conversations or experiences |
| IT Inventory | Not for human browsing; for agent grounding |
| Monitoring | No real-time metrics |
| Automation | Does not execute actions |
| Traditional CMDB | Not an IT service inventory like NetBox or ServiceNow — it is an epistemic factual substrate for agents |

---

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

---

## Roadmap

```
v1.2  →  Endpoint model, exposes/exposed_by, computed entity.runs_on
v1.1  →  Lazy integration with Hermes agents
Future →  Architectural evolution is intentionally deferred until
         empirical telemetry justifies change.
```

Current state: **BUILD MODE = OFF, OBSERVE MODE = ON**.

Specific feature planning (proposal queues, evidence engines, watchers,
multi-writer support) is intentionally absent — those concepts remain in
the deferred-indicators section of `governance.md`. They enter the
roadmap **only after** the 5 primary indicators produce evidence that
contradicts current assumptions.

---

## Quick Start

```bash
git clone https://github.com/sowerkoku/knowledge-kernel.git
cd knowledge-kernel

# Use Hermes venv, not system Python
~/.hermes/hermes-agent/venv/bin/python3 -m pip install -e .

export CMDB_DATA_DIR=~/knowledge/knowledge-kernel

# Verify
python3 -c "from cmdb.api import cmdb_get; print(cmdb_get('ollama').entity.runs_on)"
# → app-server-01
```

---

## Documentation

The documentation is organized in three levels of abstraction:

```
README.md (this file)
 ├── philosophy.md       ← why it exists, principles, KPIs
 └── architecture.md    ← how the pieces connect

 domain-model.md    ← what entities represent
 schema-v1.md        ← how entities are serialized
 usage-patterns.md   ← how to query it
 governance.md       ← what belongs to the Kernel
 audit-methodology.md ← how to verify quality
 error-log.md        ← how it fails
 github-metadata.md  ← repo metadata
```

**For contributors:**
- Start at README → philosophy → architecture
- Implement with: domain-model → schema-v1 → usage-patterns
- Operate with: governance → audit-methodology → error-log

---

## License

MIT — Kernel Maintainer, 2026