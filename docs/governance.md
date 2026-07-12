# Governance — knowledge-kernel Knowledge Kernel

**Purpose:** Rules for what enters the Kernel, what does not, and how the Kernel evolves.

---

## 1. Survival Test (official filter)

An entity belongs in the Kernel if it passes these 3 queries without free text:

```python
cmdb_get("X")           # Can the Kernel tell me if X exists?
cmdb_impact("X")        # Can the Kernel tell me what breaks if X fails?
cmdb_validate()          # Is everything coherent?
```

- ✅ **Passes all 3** → Kernel (indexable facts, navigable relations)
- ❌ **Fails any** → Wiki / ADR (narrative, context, decisions)

This means:
- Do not add kinds by anticipation
- Do not add fields by anticipation
- Do not add entities by anticipation

**The pattern is:** A real question appears that the Kernel cannot answer. Then we determine why. Then we expand.

---

## 1.5. Observe Rule 1 (Change Freeze)

**No architectural change may be introduced before observing at least 100 real queries**, unless fixing a defect or security issue.

This rule protects the project from the natural temptation to expand during usage:

> "Since we're here, let's add just one more thing..."

**Current status:**
- BUILD MODE = OFF
- OBSERVE MODE = ON
- Targets: 100–500 real queries, then evidence-guided evolution

**Permitted during freeze:**
- Expand dataset (add missing entities, relations)
- Fix bugs
- Improve documentation
- Tune performance
- Analysis of telemetry (KAR, FGR, Fact Miss Rate, API distribution)

**Not permitted during freeze:**
- New public APIs
- New indexes not triggered by observed patterns
- New engines or layers
- Proposal queues
- Evidence engines
- Auto-reload or file watchers
- Architectural redesign

This rule operationalizes the principle:

> The next architecture must emerge from observed usage patterns and empirical evidence, not anticipation.

---

## 2. What Enters the Kernel

| Criterion | Description |
|-----------|-------------|
| **Objective fact** | Something that exists in reality — not inferred |
| **Single source of truth** | Multiple agents can query it independently |
| **Relatively stable** | Does not change every minute (use monitoring for that) |
| **Queried by multiple agents** | The fact is needed by at least two agents or use cases |

**Examples of valid Kernel entities:**

| Entity | Why it belongs |
|--------|----------------|
| `ollama` | "Where does it run?" — needed before any deployment |
| `orange-pi-54` | "What runs here?" — needed for impact analysis |
| `ollama-api` | "How do agents reach Ollama?" — communication identity |
| `mysql` | "What depends on the database?" — critical dependency |

---

## 3. What Does NOT Enter the Kernel

| Category | Reason | Belongs to |
|----------|--------|------------|
| Conversational memory | Ephemeral, agent-specific | Agent memory |
| Reasoning | LLM's job — outside the Kernel | LLM |
| Inferences | Not verified — unconfirmed | LLM or inference layer |
| Real-time execution data | Changes every second — would create staleness | Monitoring |
| Internal software config | Mutable, env-specific | `.env` / `config.yaml` / Docker Compose |
| Documentation | Narrative, not fact | Wiki / README / docs |

---

## 4. Separation: Kernel ≠ Wiki / ADR

**The Kernel answers:**
- Does it exist?
- Where is it?
- What depends on what?
- How do I access it?
- What is the impact?
- Is it fresh?

**The Kernel does NOT answer:**
- Why was X decided?
- What alternatives were evaluated?
- Who made the decision?
- What changed since then?

The Wiki / ADR documents the "why" — see `/home/carlos/proyectos/cic-v3/docs/decisions/decision_log.md`.

---

## 5. The Strategic Question

> If I disappear for a week, could someone operate the CIC using only the Kernel + Runbooks?

This question determines which gaps are truly critical and which are optional improvements.

---

## 6. Evolution by Evidence, Not Anticipation

The Kernel grows when evidence demands it — not anticipation.

**Good justification:**
> *"Fact Coverage in infrastructure is low. We cannot answer 'What runs on orange-pi-54?' without manually checking. Adding 3 assets and 8 software entities solves the gap."*

**Bad justification:**
> *"We could add 50 more entities to make it more complete."*

---

## 7. Criticality Standard

```yaml
criticality:
  business: low | medium | high      # Impact on core business operations
  operational: low | medium | high    # Impact on daily operations
  technical: low | medium | high     # Recovery complexity — time/cost
```

### Classification matrix

| business | operational | technical | Classification | Action |
|-----------|-------------|-----------|----------------|--------|
| high | high | any | **CRITICAL** | Mandatory redundancy, 24/7 monitoring, documented runbook |
| high | medium | low | **IMPORTANT** | Active monitoring, scheduled backup, alerts configured |
| low | any | any | **MINOR** | Reactive maintenance, basic documentation |

---

## 8. Evidence Quality Policy

Every entity must have an `evidence` block with:

- `source_file` — where this fact was declared
- `confidence_level` — HIGH / MEDIUM / LOW / UNKNOWN
- `confidence_basis` — at least one of the five basis types
- `observed_at` — when the fact was verified (ISO-8601)

**Confidence basis definitions:**

| Basis | When to use |
|-------|-------------|
| `SCHEMA_VALIDATED` | Passed YAML schema validation |
| `HUMAN_DECLARED` | Intentionally declared by a known operator |
| `RUNTIME_CHECKED` | Verified via SSH, curl, health check |
| `INFERRED` | Deduced from other facts (mark explicitly) |
| `DISCOVERED` | Found by automated scanner, not yet validated |

**Rule:** `RUNTIME_CHECKED` and `HUMAN_DECLARED` together produce `HIGH` confidence. `DISCOVERED` alone produces `LOW`.

---

## 9. Staleness and Freshness

The Kernel records `observed_at`. It derives freshness at query time.

If a fact's freshness has expired (TTL exceeded), agents should be warned:

```python
fact = cmdb_get("ollama")
if not fact.evidence.is_fresh():
    print(f"WARNING: Ollama fact is stale — last verified {fact.evidence.observed_at}")
```

**Domain TTL defaults:**

| Domain | TTL |
|--------|-----|
| Infrastructure | 1 hour |
| Endpoints | 5–15 minutes |
| Software | 24 hours |
| Policies | 30 days |
| Procedures | 90 days |

---

## 10. Change history

| Date | Decision | Reason |
|------|----------|--------|
| v1.0 | Separate `depends_on` (BFS) from `runs_on` (1-hop) | Avoid false inferences |
| v1.0 | Normalize output: `sorted(set(...))` | Deterministic responses |
| v1.2 | Registry → Knowledge Kernel | Re-position from inventory tool to factual substrate for agents |
| v1.2 | Endpoint as identity, not URL | host/port/protocol may change without changing communication identity |
| v1.2 | `entity.runs_on` computed from relations | Single source of truth for location |
| v1.2 | Freshness computed, never stored | Prevent stale values |

Full decision log: `/home/carlos/proyectos/cic-v3/docs/decisions/decision_log.md`

---

## References

**Authoritative sources:**
- [`philosophy.md`](./philosophy.md) — Principles: "Is it a fact?", "Only what verifies facts", survival test
- [`domain-model.md`](./domain-model.md) — Entity inclusion criteria (Impact First)

**Related:**
- [`audit-methodology.md`](./audit-methodology.md) — How to audit the Kernel