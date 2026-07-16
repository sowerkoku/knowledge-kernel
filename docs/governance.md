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

| Allowed | Clarification |
|---------|---------------|
| Expand dataset (add missing entities, relations) | **Not** considered architectural change — it is empirical learning (Fact Miss Rate → new entity) |
| Fix bugs | Defects only — no opportunistic refactoring |
| Improve documentation | Always permitted |
| Performance tuning | **Only** if it preserves public contracts and architectural boundaries. Forbidden: new caches, new indexes, prefetching, watchers, new layers. |
| Analysis of telemetry | KAR, FGR, Fact Miss Rate, API distribution, dataset churn |

**Not permitted during freeze:**
- New public APIs
- New indexes not triggered by observed patterns
- New engines or layers
- Proposal queues
- Evidence engines
- Auto-reload or file watchers
- Architectural redesign
- Performance optimizations that introduce new abstractions

This rule operationalizes the principle:

> The next architecture must emerge from observed usage patterns and empirical evidence, not anticipation.

**The purpose of OBSERVE MODE is not to prove that the current architecture is correct. Its purpose is to discover where reality disagrees with our assumptions.**

---

### 1.5.1. Observation Objectives (per metric, per indicator)

The freeze is not passive. During the 100–500 query window, we actively measure five indicators.

#### A. Adoption

| Indicator | Question | Target |
|-----------|----------|--------|
| **KAR** (queries using Kernel / queries needing facts) | ¿Hermes consulta el Kernel cuando debería? | > 80% |

If KAR is low, the issue is **integration drift**, not architecture.

#### B. Grounding Quality

| Indicator | Question | Target |
|-----------|----------|--------|
| **FGR** (grounded assertions / total assertions) | ¿Las afirmaciones realmente están respaldadas? | > 90% |

If FGR is low, the issue is **agent discipline**, not architecture.

#### C. Dataset Sufficiency

| Indicator | Question | Source |
|-----------|----------|--------|
| **Fact Miss Rate** per fact-id | ¿Falta conocimiento? | `cmdb_exists(X) == False` returns |
| **Hotspot misses** | ¿Qué entidades faltan más? | log analysis |

Missing facts come from observation; they are **not** architectural change. They are empirical learning.

#### D. Usage Patterns

| Indicator | Question | Signal |
|-----------|----------|--------|
| **API distribution** | ¿Cómo razonan los agentes? | e.g. cmdb_get 70%, cmdb_search 20%, cmdb_impact 8%, cmdb_list 2% |

If the distribution contradicts our assumptions, we learn about **actual reasoning patterns**, not about required indexes.

#### E. Dataset Churn (using `dataset_hash`)

| Indicator | Question | Target |
|-----------|----------|--------|
| **`dataset_hash` changes/day** | ¿El estado factual es estable o cambia constantemente? | **Context-dependent** |

`dataset_hash` changes/day is **not** a unilateral "lower is better" metric. Interpretation depends:

| Scenario | Expected churn |
|----------|---------------|
| Stable domestic infra, no new findings | ≈ 0 (normal) |
| Active discovery week + curation | > 0 (normal) |
| Core/infra edits with no discovery | ≈ 0 (expected) |
| High volatile hardware discovery (ports, IPs) | > 0 (signals domain TTL underestimation) |

Read this indicator **together with:**
- Number of new entities added
- Number of corrections applied
- Nature of changes (new vs. evolved vs. rotated)

This becomes useful later when we ask: *Is the current `dataset_hash` still valid?* or *What changed between hash H1 and H2?*

---

### Reading the indicators together

```
KAR high + FGR high + Miss Rate high    → Kernel coverage gap (add entities)
KAR high + FGR high + Miss Rate low     → Healthy
KAR high + FGR low                      → Agent discipline (not architecture)
KAR low                                 → Integration bug (not architecture)
```

Architecture changes are only justified by:

> "Five indicators analyzed across N queries show [pattern X] which contradicts [assumption Y]."

Not by:

> "We could make it faster / simpler / prettier."

---

### 1.5.2. Deferred indicators (roadmap only — NOT L2.1 work)

The following indicators are **annotated** here so future implementers do not lose context, but they must **not** be implemented during OBSERVE MODE.

| Indicator | Question | Reason to defer |
|-----------|----------|-----------------|
| **Fact Concentration** | ¿El 80% de las consultas dependen del 20% de las entidades? | Reveals cognitive SPOFs and curation priorities — valuable after we have volume + distribution |

Other indicators to consider in later phases (also deferred):
- Cross-agent dedup rate (how often do multiple agents query the same fact?)
- Reverse-relation necessity (how often does `cmdb_impact` use the inverse direction?)
- Discovery yield (what fraction of discovered-but-uncurated findings become curated?)

These become relevant only after the 5 primary indicators show stable patterns in production traffic.

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
| `app-server-01` | "What runs here?" — needed for impact analysis |
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

The Wiki / ADR documents the "why" — see `~/proyectos/cic-v3/docs/decisions/decision_log.md`.

---

## 5. The Strategic Question

> If I disappear for a week, could someone operate the CIC using only the Kernel + Runbooks?

This question determines which gaps are truly critical and which are optional improvements.

---

## 6. Evolution by Evidence, Not Anticipation

The Kernel grows when evidence demands it — not anticipation.

**Good justification:**
> *"Fact Coverage in infrastructure is low. We cannot answer 'What runs on app-server-01?' without manually checking. Adding 3 assets and 8 software entities solves the gap."*

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

Full decision log: `~/proyectos/cic-v3/docs/decisions/decision_log.md`

---

## 11. Documentation size governance

Documentation tends to grow by accumulation and duplication. To prevent
the SKILL.md from regressing to the 1,700-line state captured in L2.1:
**a single file is bounded**.

### Hard limits

| File                              | Maximum lines |
|-----------------------------------|--------------:|
| `SKILL.md` (in this skill)        | 500           |
| `docs/<topic>.md`                 | 500           |
| `docs/pitfalls/<single-pitfall>.md` | 200          |
| `docs/playbooks/<recipe>.md`      | 400           |
| `docs/history/*.md`               | no limit (historical) |

### What to do when a file exceeds its limit

1. **Divide by responsibility.** Split content into siblings — never append
   sections to make a bloated file "fit".
2. **Never add sections at the end** to preserve the prior structure. New
   content either creates a sibling file or replaces an existing section
   wholly.
3. **Never duplicate a heading.** A repeated section title in the same file
   is a signal the work belongs elsewhere.

### Acceptance test

Before merging a documentation change, run the governance test in
`tests/test_doc_governance.py`. CI must remain green.

---

## References

**Authoritative sources:**
- [`philosophy.md`](./philosophy.md) — Principles: "Is it a fact?", "Only what verifies facts", survival test
- [`domain-model.md`](./domain-model.md) — Entity inclusion criteria (Impact First)

**Related:**
- [`audit-methodology.md`](./audit-methodology.md) — How to audit the Kernel