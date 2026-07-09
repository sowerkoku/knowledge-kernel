# Philosophy — knowledge-kernel Knowledge Kernel

**What principles govern the Kernel? Why is it designed this way?**

This document is the single source of truth for design principles and KPIs. All other documents reference it.

---

## 1. The Six Principles

**1. The API is the product.**

The dataset will change. The implementation will change. The public API must not break without a strong architectural reason. Stability enables independent evolution of all consumers (Hermes, Codex, Claude Code, other agents).

**2. The Kernel stays small.**

It answers: *"Does this fact exist?"* and *"What depends on it?"*
It does not store documentation, conversations, or inferred knowledge. Those belong to other systems.

Filter for every new proposal: *Does this data help verify facts for an agent?* If not → belongs elsewhere.

**3. Metrics govern evolution.**

Expand the Kernel when evidence demands it — not anticipation.
Good: *"Fact Coverage is low in infrastructure. Adding 3 assets and 8 software entities resolves the gap."*
Bad: *"We could add 50 more entities."*

**4. Facts ≠ Evidence ≠ Reasoning.**

- **Facts** — what exists (schema-validated entity)
- **Evidence** — why we trust it (source, confidence, observed_at)
- **Reasoning** — what the LLM decides (outside the Kernel)

**5. Freshness is computed, never stored.**

The Kernel records `observed_at`. It derives `expires_at` from `observed_at + domain TTL` at query time. Stale values cannot accumulate.

**6. Every assertion requires evidence.**

If a fact is not backed by the Kernel, the agent must say so — not infer.

---

## 2. The Deterministic Contract

The Kernel is not a database. It is a contract:

> *If a fact is not in the Kernel, the agent treats it as unverified.*

This is the core identity. It shapes every design decision.

The Kernel is **not** a smart system. It is a trustworthy one. It provides inputs so agents can reason — it does not reason for them.

---

## 3. The Three-Layer Model

```
┌─────────────────────────────────┐
│             FACTS               │
│   What exists (Entity)          │
│                                 │
│   id, kind, status, metadata    │
│   NEVER: source, confidence     │
└─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│           EVIDENCE              │
│  Why we trust it (Evidence)      │
│                                 │
│  source_file, confidence_level  │
│  confidence_basis, observed_at  │
└─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│          REASONING              │
│  What agent decides (LLM)        │
│                                 │
│  Interpretation                 │
│  Recommendations               │
│  Actions                        │
└─────────────────────────────────┘
```

Separation is permanent. Facts never carry their own trust metadata. Evidence never makes decisions.

---

## 4. KPIs — Three Distinct Metrics

These measure different things. Never confuse them:

| KPI | What it measures | Formula |
|-----|-----------------|---------|
| **FGR** (Fact Grounding Rate) | Quality of the agent's use of the Kernel | Assertions backed by Kernel / total assertions |
| **Fact Coverage** | Coverage of the Kernel itself | Queries resolved from Kernel / queries needing facts |
| **Fact Freshness** | How current the knowledge is | Average age of verified facts |

**FGR is the primary agent quality metric.** It answers: *"Is the agent actually using the Kernel before making claims?"*

**Fact Coverage is the primary Kernel quality metric.** It answers: *"Can the Kernel answer the questions agents actually ask?"*

**Fact Freshness is the primary staleness metric.** It answers: *"How old is the average verified fact?"*

### FGR Thresholds

| FGR | Interpretation |
|-----|---------------|
| 100% | Agent queries Kernel before every assertion |
| < 50% | Agent frequently makes unverified claims |
| ~0% | Kernel not integrated — agent uses memory |

### Coverage Thresholds

| Coverage | Interpretation |
|----------|---------------|
| > 80% | Kernel is production-ready for that domain |
| 50–80% | Gaps exist — measure before expanding |
| < 50% | Kernel is incomplete — expand before trusting |

---

## 5. Response States

Every assertion in an agent's response should be classifiable:

| State | Description |
|-------|-------------|
| `verified` | Confirmed by the Kernel — entity exists with evidence |
| `observed` | Confirmed by runtime tools (SSH, curl) — not in Kernel yet |
| `inferred` | Deduced by the LLM — marked explicitly as not verified |
| `unknown` | No information available — agent must say so |

**Rule:** Never present an `inferred` fact as `verified`.

---

## 6. Identity vs Observation

This distinction is central to the endpoint model:

**Identity** — stable, permanent, the thing itself:
```yaml
id: ollama-api        # stable — never changes
```

**Observation** — may change without changing identity:
```yaml
metadata:
  host: 192.168.1.54   # observed — may change (migration, TLS, load balancer)
  port: 11434          # observed — may change
  protocol: http       # observed — may change
```

Tomorrow `ollama-api` can be `https://ollama.internal:443` and still be `ollama-api`. The **identity** is the communication contract. The **observations** are how it is currently implemented.

This principle applies beyond endpoints:
- `observed_at` — when we observed the fact (observation)
- `id` — permanent identity of the entity

---

## 7. The Lazy Integration Principle

The Kernel is **not loaded at agent startup**. It is consulted when needed.

```
Agent startup:  No cmdb calls
User question:  Does this need facts?
      │
      ▼ Yes
cmdb_get() or cmdb_list()
      │
      ▼
Kernel response
      │
      ▼
LLM Reasoning
      │
      ▼
Grounded answer
```

Benefits:
- Fast startup (no data loading)
- Every query reflects current Kernel state
- No memory of past queries (stateless)

---

## 8. Why "Deterministic"?

Same data + same time + same API = same response.

The Kernel has no randomness:
- No probabilistic outputs
- No cached results that expire differently for different callers
- `cmdb_impact(X)` returns the same graph for all callers at the same moment

This is what makes the Kernel trustworthy: multiple agents querying the same fact get the same answer.

---

## 9. Why Not RAG or Memory?

These are the most common misconceptions. The tables below are canonical.

### Why not RAG?

| RAG | knowledge-kernel |
|-----|-----------|
| Similarity search | Deterministic lookup |
| Documents | Facts |
| Probabilistic retrieval | Exact retrieval |
| Chunk embeddings | Structured entities |
| Agent-specific context | Shared factual substrate |

RAG finds *similar documents*. The Kernel answers *"Does this fact exist?"* and *"What depends on it?"*.

### Why not Agent Memory?

| Agent Memory | knowledge-kernel |
|--------------|-----------|
| Experiences | Facts |
| Conversations | Verified knowledge |
| Subjective | Objective |
| Personal | Shared across agents |
| Mutable | Evidence-backed |

Memory stores *what happened*. The Kernel stores *what is true*.

---

## See also

- [`README.md`](../README.md) — Project overview and quick start
- [`architecture.md`](./architecture.md) — How the pieces connect (Repository → Skill → Dataset → Agents)
- [`domain-model.md`](./domain-model.md) — What entities represent (Asset / Software / Endpoint / Evidence)
- [`schema-v1.md`](./schema-v1.md) — How entities are serialized (YAML schema)
- [`governance.md`](./governance.md) — What belongs to the Kernel (survival test, evidence policy)