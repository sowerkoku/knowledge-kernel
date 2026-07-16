# Domain Model — knowledge-kernel Knowledge Kernel

**Version:** 1.2 (locked — 2026-07-07)
**Status:** Factual contract — reflects production API

---

## 1. What is an entity?

> An entity exists if it has its own identity and generates value in answering operational questions or impact analysis.

### Inclusion criteria

| Criterion | Description | Example ✅ | Example ❌ |
|-----------|-------------|------------|------------|
| **Stable identity** | Has a stable, queryable `id` | `ollama`, `app-server-01` | `run-20260622`, `session-abc` |
| **Operational query** | Answers production questions | "Where does X run?", "What depends on it?" | README, documentation |
| **Impact analysis** | Participates in failure chains — its state affects others | "What breaks if this fails?" | Ephemeral config |

### Principle: Impact First

> **Every new entity must justify what query or impact analysis cannot be resolved without it.**

If it does not improve queries or impact analysis, it is configuration — not an entity.

---

## 2. Entity types (catalog)

| Kind | Description | Examples |
|------|-------------|----------|
| `asset` | Physical or virtual host (servers, routers, PCs) | `app-server-01`, `pos-server-01` |
| `software` | Executing process or service (daemon, CLI, library) | `ollama`, `mysql`, `hermes` |
| `endpoint` | Observable communication identity | `ollama-api`, `telegram-bot` |
| `automation` | Scheduled scripts, jobs, pipelines | `sync-firebird-mysql` |
| `data` | Databases, backups, datasets | `firebird_db`, `backup-20260621` |

**Rule:** Do not add new `kind` until justified by operational use case (Impact First).

---

## 3. Entity model — each answers one question

```
┌─────────────────────────────────────────┐
│                  Asset                   │
│        Where does software run?          │
│        Example: app-server-01             │
└─────────────────────────────────────────┘
                    ▲
                    │ runs_on
                    │
┌─────────────────────────────────────────┐
│                Software                   │
│              What executes?              │
│        Example: ollama, mysql            │
└─────────────────────────────────────────┘
                    │
                    │ exposes
                    ▼
┌─────────────────────────────────────────┐
│               Endpoint                    │
│  How can other components communicate    │
│              with it?                     │
│                                         │
│  ID = stable identity                   │
│  host/port/protocol = observed facts     │
│  (may change without changing the ID)   │
│  Example: ollama-api → 192.168.10.10:    │
│  11434, http                             │
└─────────────────────────────────────────┘
                    │
                    │ exposed_by
                    ▼
              Evidence
         Why do we believe this?
```

| Entity | Question it answers |
|--------|---------------------|
| `Asset` | Where does it run? |
| `Software` | What executes? |
| `Endpoint` | How can other components communicate with it? |
| `Evidence` | Why do we believe this is true? |

### Identity vs Observation (key distinction)

An endpoint's **ID** is its stable identity:

```yaml
id: ollama-api        # stable — never changes
```

Its **host/port/protocol** are observed facts that may change:

```yaml
metadata:
  host: 192.168.10.10   # observed — may change (IP migration, TLS, load balancer)
  port: 11434          # observed — may change (port remapping)
  protocol: http       # observed — may change (HTTPS migration)
```

Tomorrow the endpoint can be `https://ollama.internal:443` and still be `ollama-api`.

---

## 4. Typed relations

| Relation | Semantics | Example |
|----------|-----------|---------|
| `runs_on` | Host where software executes | `ollama` runs_on `app-server-01` |
| `exposes` | Software exposes this endpoint | `ollama` exposes `ollama-api` |
| `exposed_by` | Endpoint belongs to this software | `ollama-api` exposed_by `ollama` |
| `uses` | Functional dependency — requires to operate | `hermes` uses `ollama` |
| `reads` | Reads data from source | `sync` reads `firebird_db` |
| `writes` | Writes data to destination | `sync` writes `mysql_cic` |
| `calls` | Direct HTTP/RPC invocation to endpoint | `automation` calls `telegram-api` |
| `owns` | Ownership or operational responsibility | `cico` owns `app-server-01` |
| `backs_up` | Backup or replication | `backup-nightly` backs_up `firebird_db` |
| `monitors` | Monitoring, health checks | `watchdog` monitors `ollama` |

**`runs_on` is computed from relations.** When you call `cmdb_get("ollama").entity.runs_on`, the Kernel looks for the first relation of type `runs_on` and returns its target. You do not need to store `runs_on` separately.

### Transitivity rules

| Relation | Transitive | Reason |
|----------|-----------|--------|
| `runs_on` | ❌ No | Physical location is 1-hop — does not propagate |
| `exposes` / `exposed_by` | ❌ No | Identity link — does not propagate |
| `uses` | ✅ Yes | Functional dependencies propagate |
| `reads` / `writes` | ✅ Yes | Data impact flows transitively through the pipeline |
| `calls` | ❌ No | Direct endpoint invocation — no chain |
| `owns` / `backs_up` / `monitors` | ❌ No | Direct relationship — does not propagate |

---

## 5. Usage patterns

### Scenario 1: Where does Ollama run?

```python
entity = cmdb_get("ollama")
print(entity.entity.runs_on)
# → "app-server-01"   ← computed property
```

### Scenario 2: What breaks if port 11434 fails?

```python
impact = cmdb_impact("ollama-api")
# → depends_on_me.direct: [{id: "ollama", kind: "software", relation: "exposes"}]
# → ollama.depends_on_me.direct: [{id: "open-webui", kind: "software", relation: "uses"}]
# → SPOF: True
```

Answer: *"Closing port 11434 removes Ollama → OpenWebUI loses its LLM backend."*

### Scenario 3: What uses MySQL?

```python
impact = cmdb_impact("mysql")
print(impact["depends_on_me"])
```

### Scenario 4: What runs on app-server-01?

```python
all_software = cmdb_list(kind="software")
running_here = [e["id"] for e in all_software
                if any(r["type"] == "runs_on" and r["target"] == "app-server-01"
                       for r in e.get("relations", []))]
```

---

## 6. Out of scope

**These are NOT entities:**

- Prompts, conversations, messages
- Execution logs, Git commits
- Documents (README, wikis, manuals)
- Internal software configuration
- Completed runs, temporary jobs
- User sessions, tokens, credentials

**Exception:** Any of these becomes an entity **only** if a justified operational query exists (Impact First).

---

## 7. Anti-patterns

| Anti-pattern | Symptom | Fix |
|-------------|---------|-----|
| Entity without query | "What is this for?" — no operational question it answers | Remove or convert to metadata |
| Generic relation | `depends_on: [...]` without typed semantics | Use `uses`, `reads`, `writes`, `exposes` |
| Binary criticality | `criticality: high` — no breakdown | Use `business`, `operational`, `technical` |
| Ephemeral entities | `prompt-YYYYMMDD`, `run-123` | Only if impact analysis requires it |
| `runs_on` in metadata | `metadata.runs_on: server-53` | Use `entity.runs_on` computed property |
| `endpoint` as URL | `metadata.url: http://...` without identity separation | Use `kind: endpoint` + `metadata.host/port/protocol` |

---

## 8. References

**Authoritative sources:**
- [`philosophy.md`](./philosophy.md) — Six principles, KPI definitions (FGR, Coverage, Freshness)
- [`architecture.md`](./architecture.md) — Pipeline, code vs data separation, package structure

**Related:**
- [`schema-v1.md`](./schema-v1.md) — YAML specification
- [`usage-patterns.md`](./usage-patterns.md) — Query patterns and cmdb API usage
- [`governance.md`](./governance.md) — What enters the Kernel, what does not

---

## Change history

| Date | Version | Change |
|------|---------|--------|
| 2026-06-22 | draft | Initial contract — domain model v1 |
| 2026-07-07 | v1.2 | Full rewrite: Asset→Software→Endpoint→Evidence, exposes/exposed_by, entity.runs_on computed, endpoint identity vs observation |