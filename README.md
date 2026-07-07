# Agent-CMDB

**Una capa de memoria factual para agentes de IA.**

> "A factual knowledge layer for AI agents."

---

## Data Directory

⚠️ **`data/` is a development/example dataset.** It is included for testing and demonstration.

**Production users:** Set your own knowledge dataset via:
```bash
export CMDB_DATA_DIR=~/knowledge/agent-cmdb
```

The tool is reusable — you bring your own dataset.

---

## The Problem

**LLMs have knowledge. Agents need reality.**

Reality changes:
- Servers move
- Services fail
- Dependencies evolve
- Configurations become stale

**Memory alone is not enough.**

An agent that "remembers" infrastructure will:
- ❌ Invent servers that don't exist
- ❌ Forget critical dependencies
- ❌ Assume outdated configurations
- ❌ Repeat questions across sessions
- ❌ Lose knowledge between conversations

An agent that **queries reality** before acting will:
- ✅ Ground responses in verified facts
- ✅ Express uncertainty explicitly
- ✅ Cite sources properly
- ✅ Understand impact before modifying
- ✅ Maintain knowledge across sessions

---

## The Solution

**Agent-CMDB provides:**

```
User
  │
  ▼
AI Agent
  │
  │ Query facts
  ▼
┌──────────────┐
│ Agent-CMDB   │ ← Factual Memory Layer
└──────────────┘
  │
  ├─ Entity       → What exists
  ├─ Evidence     → Why we trust it
  ├─ Context      → When queried
  └─ Impact Graph → What breaks if it changes
  │
  ▼
Grounded Response
```

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Factual Entities** | Typed, structured facts about infrastructure |
| **Typed Relationships** | `runs_on`, `uses`, `reads`, `writes`, `calls`, etc. |
| **Evidence Tracking** | Source, validation status, confidence level |
| **Freshness Information** | When observed, when expires, TTL by source type |
| **Impact Analysis** | Dependency graph: "What breaks if X fails?" |
| **Change Detection** | Entity hashes to detect modifications |

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/sowerkoku/agent-cmdb.git
cd agent-cmdb

# Create virtual environment (required on Debian/Ubuntu)
python3 -m venv .venv
source .venv/bin/activate

# Install package
pip install -e .
```

**Verify installation:**

```bash
python -c "from cmdb import cmdb_get; print('✓ Agent-CMDB installed')"
```

### Usage

```python
from cmdb.api import cmdb_exists, cmdb_get, cmdb_impact
```

### Configuration

```bash
# Set your knowledge dataset location (default: ~/.local/share/agent-cmdb)
export CMDB_DATA_DIR=~/knowledge/agent-cmdb
```

Or in Python:
```python
import os
os.environ["CMDB_DATA_DIR"] = "~/knowledge/agent-cmdb"
```

# 1. Check existence BEFORE making factual claims
```
if cmdb_exists("ollama").exists:
    print("✓ Ollama exists in CMDB")
else:
    print("✗ Ollama not found — cannot verify this claim")
```

# 2. Get entity with full evidence
```
result = cmdb_get("ollama")
print(f"Ollama is {result.entity.kind}")
print(f"Source: {result.evidence.source_file}")
print(f"Confidence: {result.evidence.confidence_level}")
print(f"Fresh until: {result.evidence.expires_at}")
```

# 3. Check impact BEFORE modifying
```
impact = cmdb_impact("ollama")
print(f"{len(impact['depends_on_me']['direct'])} entities depend on Ollama")
print(f"Single point of failure: {impact['risk_indicators']['single_point_of_failure']}")
```

---

## Example: Agent Behavior Change

### ❌ Before Agent-CMDB

**User:** "Can I upgrade Ollama?"

**Agent:**
> "I think Ollama is only used by the local model. Should be safe to upgrade."

*(Agent relies on memory, invents facts, no impact analysis)*

---

### ✅ With Agent-CMDB

**User:** "Can I upgrade Ollama?"

**Agent:**
```python
# Step 1: Verify existence
fact = cmdb_get("ollama")
assert fact.exists

# Step 2: Check impact
impact = cmdb_impact("ollama")

# Step 3: Ground response
print(f"**Facts about Ollama:**")
print(f"- Runs on: {fact.entity.metadata.get('runs_on')}")
print(f"- Status: {fact.entity.status}")
print(f"- Confidence: {fact.evidence.confidence_level}")
print()
print(f"**Impact Analysis:**")
print(f"- {len(impact['depends_on_me']['direct'])} entities depend on Ollama")
print(f"- Dependents: {', '.join(d['id'] for d in impact['depends_on_me']['direct'])}")
print(f"- Single point of failure: {impact['risk_indicators']['single_point_of_failure']}")
print()
print(f"**Risk: HIGH**")
print(f"No redundancy configured. Upgrading Ollama will affect:")
print(f"- {len(impact['risk_indicators']['critical_dependents'])} critical dependents")
print(f"\nRecommendation: Schedule maintenance window, notify users first.")
```

**Output:**

> **Facts about Ollama:**
> - Runs on: server-53
> - Status: operational
> - Confidence: high (schema_validated, human_declared)
>
> **Impact Analysis:**
> - 5 entities depend on Ollama
> - Dependents: hermes-arquitectobi, hermes-ingenierosql, hermes-webon, hermes-qaconsistencia, open-webui
> - Single point of failure: True
>
> **Risk: HIGH**
>
> No redundancy configured. Upgrading Ollama will affect:
> - 3 critical dependents
>
> **Recommendation:** Schedule maintenance window, notify users first.

---

## Architecture

### Three-Layer Separation

```
┌─────────────────────────────────┐
│           FACTS                 │
│  What exists (Entity)           │
│  - id, kind, status, metadata   │
│  NEVER includes: source, trust │
└─────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│         EVIDENCE                │
│  Why we trust it (Evidence)     │
│  - source, validation, hash     │
│  - confidence level + basis     │
│  - observed_at, expires_at      │
└─────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│        REASONING                │
│  What agent decides (LLM)       │
│  - Interpretation               │
│  - Recommendations              │
│  - Actions                      │
└─────────────────────────────────┘
```

### Key Design Principles

1. **Facts ≠ Evidence ≠ Reasoning**
   - Facts: What exists (schema-validated)
   - Evidence: Why we trust it (source, confidence)
   - Reasoning: Agent's interpretation (LLM decides)

2. **Temporal Awareness**
   - `observed_at`: When fact was verified
   - `expires_at`: When confidence expires
   - `invalidated_at`: When fact became invalid
   - Agents can detect staleness

3. **Change Detection**
   - Entity hashes (SHA256[:16])
   - Compare between queries
   - Know if facts changed

4. **Impact-First**
   - Always check `cmdb_impact()` before modifying
   - Dependency graph prevents accidents
   - Risk indicators guide decisions

---

## API Reference

### Core Functions

| Function | Purpose | When to Use |
|----------|---------|-------------|
| `cmdb_exists(entity_id)` | Check if entity exists | **ALWAYS** before any factual claim |
| `cmdb_get(entity_id)` | Get entity + evidence | Deep reasoning about specific entity |
| `cmdb_assert(entity_id, kind, status)` | Binary validation | Decision requires specific state |
| `cmdb_context(agent_id)` | Pre-packaged agent context | Agent startup (1 call vs 20 queries) |
| `cmdb_search(query)` | Find entities | When entity ID unknown |
| `cmdb_impact(entity_id)` | Dependency analysis | **ALWAYS** before modifying anything |

### Example: Agent Initialization

```python
# Single call provides complete self-knowledge
ctx = cmdb_context("hermes-arquitectobi")

print(f"I am: {ctx['identity']}")
print(f"I run on: {ctx['known_environment']['runs_on']}")
print(f"I use: {ctx['known_environment']['uses']}")
print(f"Dependents: {ctx['dependents']}")
print(f"Warnings: {ctx['warnings']}")
```

---

## Confidence Levels

Agent-CMDB does **NOT** measure truth probability.

It measures **evidence quality**.

| Level | Meaning | When Used |
|-------|---------|-----------|
| `high` | Multiple strong signals | Schema validated + human declared + recent |
| `medium` | Single strong signal OR multiple weak | Schema validated OR human declared |
| `low` | Weak or incomplete evidence | Auto-discovered, no validation |
| `unknown` | Minimal or no evidence | Unknown origin |

### Evidence Basis

Why we trust this fact:

| Basis | Description |
|-------|-------------|
| `schema_validated` | Passed YAML schema v1 validation |
| `human_declared` | Intentionally declared by human |
| `runtime_checked` | Verified at runtime (health check) |
| `inferred` | Deduced from other facts |
| `discovered` | Auto-discovered by scanner |

**Example:**

```json
{
  "confidence": {
    "level": "high",
    "basis": ["schema_validated", "human_declared"]
  }
}
```

---

## What Agent-CMDB Is NOT

| Non-Goal | Why |
|----------|-----|
| ❌ IT inventory system | Not for human browsing; for agent grounding |
| ❌ Monitoring solution | Doesn't track real-time metrics |
| ❌ Automation engine | Doesn't execute actions |
| ❌ LLM memory replacement | Doesn't store conversational history |
| ❌ Knowledge base | Not for documentation or narratives |

**If you need:**
- Human UI → Use NetBox, ServiceNow, etc.
- Metrics/Alerts → Use Prometheus, Grafana
- Job Execution → Use Ansible, Terraform
- Chat Memory → Use vector database

**If you need:**
- Agents that don't hallucinate infrastructure
- Verifiable facts with evidence
- Impact analysis before changes
- Temporal tracking of facts

→ Agent-CMDB is for you.

---

## Why Not a Vector Database?

**Common question:** "Why not store facts in a vector DB?"

**Answer:** Vector memory stores **information**. Agent-CMDB stores **facts**.

| Vector Database | Agent-CMDB |
|-----------------|------------|
| "Something related to Ollama" | "Ollama exists, runs_on server-53" |
| Similarity search | Exact match on `id` |
| Probabilistic | Deterministic |
| No structure | Typed schema |
| No evidence | Explicit source + confidence |
| No temporal tracking | observed_at, expires_at |
| No impact graph | Full dependency analysis |

**Use both:**
- Vector DB: Agent memory, conversation history
- Agent-CMDB: Grounding in reality

---

## Schema v1

Entities follow strict schema:

```yaml
schema_version: 1
id: ollama
kind: software

metadata:
  name: Ollama
  description: Local LLM server
  version: "0.5"

status: operational

relations:
  - type: runs_on
    target: server-53
  - type: uses
    target: docker

criticality:
  business: high
  operational: high
  technical: medium

tags:
  - llm
  - inference
```

**Validation:**

```bash
python -m cmdb.validator
# 0 errors, 72 entities validated
```

---

## Development

### Run Tests

```bash
cd integrations/hermes/tests
python -m pytest -v
# 13 tests passing
```

### Validate Entities

```bash
python -m cmdb.validator
```

### Migration (v0 → v1)

```bash
# Dry-run (preview changes)
python -m cmdb.migrator --dry-run

# Apply migration
python -m cmdb.migrator --apply
```

---

## Roadmap

### Q3 2026

- [ ] Auto-discovery (Docker, Kubernetes, Cloud APIs)
- [ ] Auto-invalidation (webhook on config change)
- [ ] GraphQL API
- [ ] Web UI (read-only, for debugging)

### Q4 2026

- [ ] Multi-agent support
- [ ] Conflict resolution (multiple sources)
- [ ] Audit log (who changed what, when)

---

## License

MIT License — see `LICENSE` file.

---

## Citation

If you use Agent-CMDB in your research:

```bibtex
@software{agent-cmdb-2026,
  title = {Agent-CMDB: A Factual Memory Layer for AI Agents},
  author = {Carlos Cáceres},
  year = {2026},
  url = {https://github.com/sowerkoku/agent-cmdb}
}
```

---

## Acknowledgments

- Inspired by Configuration Management Databases (CMDB)
- Grounding techniques from AI safety research
- Temporal reasoning from knowledge graph literature
- Agent architecture from LangChain, AutoGen, CrewAI

---

**Built with ❤️ by [@sowerkoku](https://github.com/sowerkoku)**
