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

## 8. The Four-Layer Epistemology

The Kernel implements a strict separation of epistemic responsibilities:

```
┌──────────────────────────────────────────────────────────────┐
│  Reality           │  What is the actual state of the world? │
│  (unfiltered)      │  No interpretation. No structuring.      │
├────────────────────┼─────────────────────────────────────────┤
│  Evidence          │  What did we observe and how?           │
│  (observations)    │  Source, method, timestamp, confidence.  │
│                    │  Not yet a claim — just captured data.   │
├────────────────────┼─────────────────────────────────────────┤
│  Facts             │  What verified claims can we defend?    │
│  (structured)     │  Entities + Relations + Identity vs     │
│                    │  Observation distinction.               │
├────────────────────┼─────────────────────────────────────────┤
│  Grounded Reasoning│  What follows from the facts?          │
│  (agent layer)     │  Query Kernel → Reason deterministically │
│                    │  → Act. Never alter facts here.         │
└──────────────────────────────────────────────────────────────┘
```

**The center of the system is Evidence, not Entities.** Entities are types of facts. The Kernel does not store data — it stores evidence-backed claims about reality.

### The Three Emergent Properties

These are not independent features. They form a reinforcing chain:

```
Reproducibility
       ↓
Auditability    ← If a fact can be reproduced, it can be audited
       ↓
Determinism     ← If it can be audited, agents arrive at the same fact
```

**Reproducibility:** Every fact carries provenance (discovered_by + discovery_method + discovery_run) so any observation can be re-executed. `provenance.discovery_run` enables this.

**Auditability:** Every fact answers: What do we know? Why do we believe it? When was it observed? How was it discovered? Who incorporated it?

**Determinism:** Two agents with the same Kernel state, querying the same fact, obtain the same answer. Same data, same time, same result — every time.

---

### Invariants of `dataset_hash`

The `dataset_hash` (SHA256[:8] of canonical YAML content) obeys three invariants:

**Invariant 1 — Stability**
```
Same dataset
    ⇒ same dataset_hash
```
If no YAML content changes, the hash remains identical across reloads, processes, and time.

**Invariant 2 — Sensitivity**
```
Different dataset contents
    ⇒ different dataset_hash
```
Any change to canonical YAML (add, edit, delete) will change the hash. This makes it a content-addressed identifier.

**Invariant 3 — Independence from runtime state**
```
Same dataset_hash
    ⇏ same engine_generation
```
You can reload the engine 10 times without changing YAML — the hash stays the same, but `engine_generation` increments. The hash represents **factual identity**, not operational state.

These invariants ensure that `dataset_hash` is suitable for:
- Reproducibility (Invariant 1)
- Auditability (Invariant 2)
- Temporal correlation (Invariant 3)

---

## 9. The Eight Operational Rules

Organized by purpose:

**Honestidad** — keep the Kernel epistemologically clean:

| # | Rule |
|---|------|
| 1 | Entity existence ≠ Entity running |
| 2 | No fact without evidence |
| 3 | No inference from naming conventions |

**Gobernanza** — controlled, auditable evolution:

| # | Rule |
|---|------|
| 4 | Discovery proposes, humans curate, Kernel records |
| 5 | Active dataset has no version number. Snapshots do. |
| 6 | Entry criteria enforced (exists + evidence + observed property + observed_at + provenance + valid relations) |

**Temporalidad y trazabilidad** — temporal integrity:

| # | Rule |
|---|------|
| 7 | Facts are replaceable; evidence is append-only |
| 8 | Every fact is reproducible from its evidence |

**Auditability** — every grounded claim attributable to evidence:

| # | Rule |
|---|------|
| 9 | Every grounded assertion SHOULD be reproducibly attributable to a specific `dataset_hash` |

Rule 9 does not require the agent to do anything special — `cmdb_get()` and
`log_assertion()` automatically capture the current `dataset_hash` and
`engine_generation`. The rule formalizes the property that any grounded claim
made by an agent can be tied back to the exact canonical state of the
Knowledge Kernel that supported it — and can be **reproduced** under that
state.

The three properties are linked:

```
Reproducibility   ← Given dataset_hash, the same query yields the same answer
        ↓
Auditability      ← Who asserted, what, supported by which facts
        ↓
Determinism       ← Two agents under the same dataset_hash get the same answer
```

This converts every assertion into an auditable event: *who* asserted,
*what* was asserted, *which facts* supported it, and *under which dataset
state* those facts were current.

---

## 10. A Maturity Model for the Kernel

KPIs map to four levels of Kernel maturity:

**Nivel 1 — Disponibilidad (Coverage)**

| KPI | Question |
|-----|----------|
| Fact Coverage | ¿Existe conocimiento suficiente? |
| Provenance Coverage | ¿Sabemos de dónde viene cada hecho? |

**Nivel 2 — Calidad (Quality)**

| KPI | Question |
|-----|----------|
| DQS (Dataset Quality Score) | ¿Los hechos están bien modelados? |
| Reproduction Rate | ¿Podemos volver a verificar cada hecho? |

**Nivel 3 — Operación (Freshness)**

| KPI | Question |
|-----|----------|
| FFR (Fresh Fact Ratio) | ¿Sigue siendo válido hoy? |

**Nivel 4 — Adopción (Usage)**

| KPI | Question |
|-----|----------|
| FGR (Fact Grounding Rate) | ¿Los agentes realmente lo utilizan? |

### Kernel Health Index

```
KHI = Coverage × Quality × Freshness × Adoption
```

All four dimensions must be healthy. A high-coverage, low-quality Kernel is dangerous — agents reason on facts that cannot be defended. A high-quality, low-freshness Kernel becomes stale. A perfectly fresh, unused Kernel has zero value.

---

## 11. What the Kernel Is Not

The definition has evolved:

| Era | What it was | What it asked |
|-----|-------------|---------------|
| Registry | Inventory | ¿Qué guardamos? |
| CMDB | Configuration facts | ¿Qué está configurado? |
| **Knowledge Kernel** | **Governed epistemic infrastructure** | **¿Qué afirmaciones estamos dispuestos a defender y por qué?** |

**A Knowledge Kernel is not a memory system.** It is not a document store, not a RAG corpus, not an agent memory bank.

It is a governed factual substrate that enables multiple agents to reason from the same reproducible and auditable view of reality. Every claim in it can be explained, reproduced, audited, and shared deterministically.

---

## 12. Future Formalization: Fact Lifecycle and Evidence Levels

Two areas are implicitly defined by the model but not yet formally codified:

### Fact Lifecycle (implicit, not yet implemented)

```
Observed → Curated → Accepted → Stale → Replaced
```

- **Observed** — Discovery found a fact; evidence captured but not yet reviewed
- **Curated** — Human reviewed evidence; fact is ready for entry
- **Accepted** — Fact is in the active Kernel with valid evidence
- **Stale** — Evidence is older than the domain TTL; needs re-verification
- **Replaced** — A newer observation superseded the fact; old evidence preserved (append-only)

This lifecycle is already implied by `observed_at`, `discovery_run`, and Rule 7 (evidence append-only), but the state machine is not yet formalized in code.

### Evidence Levels (implied, not yet codified)

```
Declared → Discovered → Verified → Corroborated
```

- **Declared** — Human assertion without verification
- **Discovered** — Captured via automated discovery (SSH, ss, docker ps)
- **Verified** — Re-run discovery confirmed the observation
- **Corroborated** — Multiple independent sources confirm the fact

The current model has `confidence: high/medium/low` in evidence blocks, but this four-level scale would enable more precise governance. Not required today — the 8 rules + DQS already provide sufficient governance. These are noted for when the Kernel reaches Maturity Level 3+.

---

## See also

- [`README.md`](../README.md) — Project overview and quick start
- [`architecture.md`](./architecture.md) — How the pieces connect (Repository → Skill → Dataset → Agents)
- [`domain-model.md`](./domain-model.md) — What entities represent (Asset / Software / Endpoint / Evidence)
- [`schema-v1.md`](./schema-v1.md) — How entities are serialized (YAML schema)
- [`governance.md`](./governance.md) — What belongs to the Kernel (survival test, evidence policy)