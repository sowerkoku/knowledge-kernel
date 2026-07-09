# Philosophy

**Why the Knowledge Kernel exists. What it is. What it is not.**

> *"It does not reason, infer, or decide."*

This is the identity of the Kernel. It is not a smart system. It is a trustworthy one. The Kernel provides inputs so agents can reason — it does not reason for them.

---

## 1. The Problem with LLMs

When an LLM answers *"Where does Ollama run?"* it:

- **Infers** from training data — often wrong
- **Mixes** facts with reasoning — no separation
- **Cannot verify** whether the answer is current
- **Does not share** a source of truth with other agents

LLMs are powerful reasoning engines built on shaky factual foundations.

**Agents need a shared factual substrate they can query, not a model that guesses.**

---

## 2. What the Kernel Is

A **deterministic factual substrate** for AI agents.

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

Three things live here:
- **What exists** (Entity)
- **Why we trust it** (Evidence)
- **When it was observed** (Freshness)

Reasoning lives elsewhere. The Kernel supplies its inputs.

### The contract

> *If a fact is not in the Kernel, the agent treats it as unverified.*

This single sentence defines the Kernel's role. Not a database. Not a memory. Not a knowledge base. A **contract**.

---

## 3. Core Distinctions

### Grounding vs Reasoning

| Grounding (Kernel) | Reasoning (LLM) |
|--------------------|-----------------|
| *Does Ollama exist?* | *Should we upgrade Ollama?* |
| *Where does it run?* | *Is it safe to do so?* |
| *What depends on it?* | *What's the impact?* |

The Kernel tells the LLM what *is*. The LLM tells the user what *should be*.

### Identity vs Observation

| Identity (stable) | Observation (mutable) |
|-------------------|----------------------|
| `id: ollama-api` | `host: 192.168.1.54` |
| The thing exists | Where it lives right now |
| Never changes | May change tomorrow |

An endpoint's ID is its **communication identity**. The host/port/protocol are its **connection details**. They are not the same thing.

### Evidence vs Inference

| Evidence (Kernel) | Inference (LLM) |
|-------------------|-----------------|
| Verified facts | Derived conclusions |
| Sources cited | Sources invented if needed |
| Confidence measured | Confidence guessed |

The Kernel records what is true. The LLM records what seems plausible. Confusing them produces hallucination.

### Freshness vs Confidence

| Freshness (Kernel) | Confidence (Kernel) |
|--------------------|---------------------|
| *Is the fact current?* | *How strong is the evidence?* |
| Computed from observed_at | Computed from basis list |
| A high-confidence fact can be stale | A fresh fact can have weak evidence |

Two orthogonal axes. Both matter.

---

## 4. The Six Principles

### 1. The API is the product

The dataset will change. The implementation will change.

But the public API (`cmdb.api`) must not break without strong architectural reason.

Stability enables independent evolution of all consumers.

### 2. The Kernel stays small

It answers: *"Does this fact exist?"* and *"What depends on it?"*

It does not store:
- Documentation (→ wiki)
- Conversations (→ memory)
- Inferences (→ LLM)
- Real-time metrics (→ monitoring)
- Configuration (→ env vars)

That discipline keeps the Kernel elegant and trustworthy.

### 3. Metrics govern evolution

Expand the Kernel when **evidence demands it** — not anticipation.

Good: *"Fact Coverage is low in infrastructure."*
Bad: *"We could add 50 more entities."*

### 4. Facts ≠ Evidence ≠ Reasoning

- **Facts** — what exists (schema-validated)
- **Evidence** — why we trust it (source, confidence, observed_at)
- **Reasoning** — what the LLM decides (outside the Kernel)

Three layers. Different responsibilities. None of them doing the other's job.

### 5. Freshness is computed, never stored

The Kernel records `observed_at`. Freshness is derived at query time from `observed_at + domain TTL`.

Nothing becomes stale — because nothing stores need-revision values.

### 6. Every assertion requires evidence

If a fact is not backed by the Kernel, the agent must say so explicitly.

> *"I cannot verify this fact — it is not in the Kernel."*

That is a valid answer. Inferring silently to fill the gap is the failure mode the Kernel prevents.

---

## 5. What the Kernel Replaces

### Old model

```
Agent
  │
  ├── Memory (LLM-internal)
  │     └── facts merged with reasoning
  │
  ├── Documentation (wiki)
  │     └── facts mixed with context, author opinions
  │
  ├── Configuration (env, config.yaml)
  │     └── facts mixed with settings
  │
  └── Monitoring (Prometheus, Grafana)
        └── facts mixed with real-time data
```

Every layer made the same kind of mistake: facts and context mixed together.

### New model

```
Agent
  │
  ├── Knowledge Kernel  ← ground truth
  │       facts + evidence + freshness
  │
  ├── Reasoning        ← interpretation (LLM)
  │       logic, planning, judgment
  │
  ├── Memory           ← experience (separate system)
  │       conversation history, preferences
  │
  ├── Configuration    ← mutable settings (env, yaml)
  │       runtime params, deployment config
  │
  └── Monitoring       ← real-time observations
        ← metrics, alerts, health checks
```

Five layers. Each with one job. Each impermeable to the others' content.

---

## 6. The Identity Statement

The Kernel is **not** smarter than an LLM. It is **trustier**.

A smart system that is sometimes wrong (LLM inference) fails more catastrophically than a simple system that is always right (Kernel facts).

This trade-off is intentional. The Kernel optimizes for **trustworthiness**, not intelligence.

> *"It does not reason, infer, or decide."*

It verifies. It serves. It stops.

---

## 7. Why This Matters

If an agent using the Kernel says something wrong, the cause is one of:

1. The fact was not in the Kernel (the agent should have said "I cannot verify")
2. The fact was stale (the agent should have warned)
3. The fact had low confidence (the agent should have said so)
4. The reasoning step was wrong (the agent is responsible)

Each cause has a clean answer. Each can be fixed. None of them involve the Kernel lying.

A standard LLM failure mode — *"the model invented a fact it could not have known"* — is **architecturally impossible** with the Kernel.

That is what makes the Kernel an infrastructure layer, not a feature.

---

## 8. The Strategic Value

The Kernel is durable because it is simple.

The APIs it exposes will evolve slowly. The principles will not. The epistemic boundary (Kernel = facts, LLM = reasoning) is the kind of decision that pays off for years.

This is the kind of layer that justifies building on top.

---

## References

- [`architecture.md`](./architecture.md) — How the parts fit together
- [`domain-model.md`](./domain-model.md) — Entity responsibilities
- [`governance.md`](./governance.md) — What enters, what does not
- [`../README.md`](../README.md) — Project manifesto