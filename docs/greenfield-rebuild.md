# Greenfield Dataset Rebuild — Rules and Process

Created 2026-07-10 after dataset v1 was archived (96 entities mixed quality → 36 curated).

---

## Why Greenfield

v1 (96 entities) had mixed evidence quality:
- Inferred IPs from IDs (wrong: `server-192-168-1-52` → assumed IP .52)
- Assumed .52 had no SSH (wrong: it does, just unreachable from this context)
- "42 software entities" mixed installed vs configured vs running
- Relationships inferred without verification

**The risk:** Knowledge Kernel with 85% correct entities → agents reason on facts partially incorrect. Worse than 45 entities that are 99% correct.

---

## The 6 Entry Rules

An entity enters the active dataset ONLY if:

1. **Exists** — it is a real, observable thing (not inferred from naming conventions)
2. **Has reproducible evidence** — evidence.source + evidence.method
3. **Has at least one observed property** — a real metadata field, not derived from ID
4. **Has `observed_at`** — timestamp of the observation
5. **Has `provenance`** — `discovered_by` + `discovery_method` + `discovery_run`
6. **All relations point to existing entities** — no dangling references

If an entity fails any condition → it stays out until verified.

---

## The 7 Operational Rules

| # | Rule |
|---|------|
| 1 | Entity existence ≠ Entity running |
| 2 | No fact without evidence |
| 3 | No inference from naming conventions |
| 4 | Discovery proposes, humans curate, Kernel records |
| 5 | The active dataset has no version number. Snapshots do. |
| 6 | Entry criteria: exists + evidence + observed property + observed_at + provenance + valid relations |
| 7 | Facts are replaceable; evidence is append-only |

**Rule 8 — Every fact is reproducible from its evidence.** A fact without evidence is just a claim. A fact with evidence (source + discovery_method + observed_at + discovery_run) can be re-derived, re-verified, and re-audited. This is what transforms a YAML store into a Knowledge Kernel.

```yaml
# Without evidence — an assertion
primary_ip: 192.168.1.54

# With evidence — a reproducible fact
primary_ip: 192.168.1.54
provenance:
  discovered_by: endpoint-discovery
  discovery_method: ssh:ip_addr
  discovery_run: "2026-07-10T20:33:12Z"
evidence:
  source: "ip addr show eth0 | grep inet"
  observed_at: "2026-07-10T20:33:12Z"
  confidence: high
```

**Rule 7 — Evidence is append-only:** When a fact changes (e.g., `orange-pi-54` moves from `.54` to `.60`), the new fact replaces the old one. But the evidence trail is never overwritten. Both the old and new observation survive in the YAML history, enabling future audit: *who created this fact, how, when, and can I reproduce it?* This is the difference between a Knowledge Kernel and a simple YAML store.

---

## Discovery Run Structure

Every entity in v2 carries:

```yaml
provenance:
  discovered_by: runtime-discovery   # who/what discovered it
  discovery_method: ssh:ss            # how (protocol:tool pattern)
  discovery_run: "2026-07-10T21:34:00Z"  # when — for audit reproducibility
evidence:
  source: "ss -tlnp - LISTEN on *:3306"
  observed_at: "2026-07-10T04:47:00Z"
  confidence: high
  method:
    - ss -tlnp
    - docker inspect
```

**Why `discovery_run`?** Six months from now: who created this fact? how was it obtained? when was it observed? can I reproduce it?

---

## Deployment State (Software)

| State | Meaning |
|-------|---------|
| `installed` | Package/script present on system |
| `configured` | Configured but not running |
| `running` | Actively executing (verified via `systemctl`, `docker ps`) |
| `disabled` | Intentionally stopped |
| `retired` | Removed from active use |

These are **different things** — a Docker image installed ≠ container running.

---

## Discovery Order

```
Fase 1 — Assets (hardware/VM identity)
         SSH → hostname, uname, free -b, df -h
         Output: id, primary_ip, hostname, manufacturer, model, os, ram_gb

Fase 2 — Software (processes + containers)
         SSH → docker ps, systemctl, ps aux
         Distinguish: installed / configured / running
         Output: id, deployment_state, version (if available)

Fase 3 — Endpoints (ports + protocols)
         SSH → ss -tlnp, docker inspect
         Output: id, host, port, protocol, relations (exposed_by → software)

Fase 4 — Automation (scheduled jobs)
         crontab -l, systemctl list-timers
         Output: id, schedule, owner, relations

Fase 5 — Agents (Hermes profiles)
         Config files, NOT running state
         Output: id, deployment_state (configured, not assumed running)
```

---

## Anti-Patterns Discovered During v1

### Never infer from entity ID
```yaml
# ❌ Wrong: ID encodes a fact → tempting to decode
id: server-192-168-1-52

# ✅ Correct: explicit metadata
metadata:
  primary_ip: 192.168.1.52
```

### Never assume running state from config
```yaml
# ❌ Wrong: profile exists → assume running
deployment_state: running  # not verified

# ✅ Correct: verified state
deployment_state: configured  # exists in config, running state unknown
```

### Never use `listens_on`
```yaml
# ❌ Wrong: software "listens on" an endpoint
relations:
  - type: listens_on
    target: mariadb-endpoint

# ✅ Correct: endpoint is exposed by software
# In endpoint YAML:
relations:
  - type: exposed_by
    target: mariadb
```

---

## Dataset v2 State

```
~/knowledge/archive/knowledge-kernel-v1/   ← snapshot v1 (read-only, 96 entities)
~/knowledge/knowledge-kernel/              ← active dataset v2 (greenfield, 36 entities)

Composition:
  asset:       5  (orange-pi-54, .53, .52, servidor-pos, router)
  software:   16  (14 running SSH-verified + firebird + mysql-db-raw stubs)
  endpoint:    9  (all with host/port/protocol from ss -tlnp)
  automation:  1  (sync-firebird-mysql, schedule verified)
  agent:       5  (Hermes profiles, deployment_state=configured)
```

**KPIs:** DQS=100%, FFR=100%, valid=True, errors=0

---

## How to Run KPIs

```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel \
  python3 ~/.hermes/skills/knowledge-kernel/tools/kpi.py
```

Output: DQS, FFR, entity count by kind, validation status.

---

## Adding New Entities (The Right Way)

1. **Discover** — SSH → observe → collect evidence (source, method, observed_at)
2. **Propose** — create YAML with provenance block filled
3. **Human review** — verify evidence is reproducible
4. **Add** — move to `~/knowledge/knowledge-kernel/`
5. **Validate** — run `cmdb_validate()` → must return `valid=True`
6. **KPIs** — run `kpi.py` → DQS should stay 100%

Never auto-commit discovery output. Present diff → human approval → update.