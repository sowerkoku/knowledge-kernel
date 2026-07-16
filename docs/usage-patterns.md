# Usage Patterns — knowledge-kernel

**Purpose:** Validated query patterns. The SKILL.md has the minimal API reference.

---

## 1. Core Pattern: Fact Grounding

Every agent interaction follows this contract:

```
User question
      │
      ▼
Does this require facts?
      │
      ▼
cmdb_get("entity-id")       ← check before making any claim
      │
      ▼
Entity found? → Answer with evidence
Entity not found → "I cannot verify this — not in the Kernel"
```

**Always query before asserting.** If the Kernel does not contain a fact, the agent must say so — not infer.

---

## 2. Fact Grounding Pattern

**❌ Before knowledge-kernel**
```
Agent: "I think Ollama runs on server-53"
(Infers from training data — often wrong)
```

**✅ With knowledge-kernel**
```python
# Step 1: Verify
fact = cmdb_get("ollama")
if not fact.entity:
    print("Cannot verify — Ollama not in the Kernel")

# Step 2: Ground response
print(f"Ollama runs on {fact.entity.runs_on}")  # → app-server-01
print(f"Confidence: {fact.evidence.confidence_level}")
print(f"Evidence: {fact.evidence.confidence_basis}")
```

---

## 3. Impact Analysis Pattern

**Always check before modifying anything.**

```python
# What breaks if I change Ollama?
impact = cmdb_impact("ollama")
print(f"Direct dependents: {impact['depends_on_me']['direct']}")
print(f"SPOF: {impact['risk_indicators']['single_point_of_failure']}")
```

**Real example — port failure:**
```python
impact = cmdb_impact("ollama-api")
# Ollama-api exposed_by: ollama
# Ollama used_by: open-webui
# SPOF: True
# → Answer: "Closing port 11434 removes Ollama → OpenWebUI loses its LLM backend"
```

---

## 4. Lazy Integration Pattern

The Kernel is **not loaded at startup**. It is consulted only when needed.

```
Agent startup:  No cmdb calls
User question:  Needs facts?
      │
      ▼ Yes
cmdb_get() or cmdb_list()
      │
      ▼
Answer with grounded facts
```

This keeps startup fast and ensures every query reflects current Kernel state.

---

## 5. Context Loading Pattern

For agent initialization with full self-knowledge:

```python
from cmdb.api import cmdb_context

ctx = cmdb_context("hermes-arquitectobi")
print(f"I am: {ctx['identity']}")
print(f"I run on: {ctx['known_environment']['runs_on']}")
print(f"I use: {ctx['known_environment']['uses']}")
print(f"Dependents: {ctx['dependents']}")
print(f"Warnings: {ctx['warnings']}")  # stale facts, broken relations
```

---

## 6. Query by Kind / Domain / Status

```python
# All operational infrastructure software
cmdb_list(kind="software", domain="infrastructure", status="operational")

# All endpoints
cmdb_list(kind="endpoint")

# All assets
cmdb_list(kind="asset")

# Find entities by name/description/tags
cmdb_search("ollama")
```

---

## 7. Multi-Instance Pattern

When one software runs in multiple configurations, **each instance = separate entity**:

```yaml
# hermes-arquitectobi.yaml
id: hermes-arquitectobi
kind: software
domain: infrastructure
metadata:
  profile: arquitectobi
relations:
  - type: runs_on
    target: server-192-168-1-52
```

**Rules:**
1. Each instance = separate entity with unique ID
2. Naming: `<name>-<config>` (e.g., `hermes-arquitectobi`, not `hermes-gateway-52`)
3. Config variant stored in `metadata`, not in the ID

---

## 8. Network Diagnosis on Remote Assets

**Correct order** when diagnosing a service on a remote machine:

```
1. cmdb_list(kind="asset")              → list all machines
2. cmdb_get(asset_id)                   → get IP, SSH port, hostname
3. VERIFY NETWORK (ping/port scan)      → confirm connectivity BEFORE assuming
4. cmdb_impact(service_id)              → understand what depends on this service
5. THEN connect to the real service      → only after verifying 1-4
```

**CRITICAL PITFALL:** Do not assume a service is local. The Kernel tells you `runs_on: [asset_id]` — if the asset is not the current machine, verify network connectivity first.

```bash
# BAD — assumes MySQL is local
mysql -u root -e "SHOW DATABASES"

# GOOD — first query the Kernel
python3 -c "
from cmdb.api import cmdb_get
mysql = cmdb_get('mysql')
print(f'Host: {mysql.entity.runs_on}')
"

# Then verify connectivity before connecting
ping -c 1 -W 2 192.168.10.10
for port in 22 3306; do
    timeout 2 bash -c "echo >/dev/tcp/192.168.10.10/$port" 2>/dev/null \
        && echo "Port $port: OPEN" || echo "Port $port: CLOSED"
done

# Then connect
mysql -h 192.168.10.10 -u agente -p -e "SHOW DATABASES"
```

---

## 9. Asset Dependency Query

What runs on a specific asset?

```python
all_software = cmdb_list(kind="software")
running_here = [
    e["id"] for e in all_software
    if any(
        r["type"] == "runs_on" and r["target"] == "app-server-01"
        for r in e.get("relations", [])
    )
]
```

---

## 10. Container Port Discovery

Containers with `--network=host` do not appear in `docker ps --format "{{.Ports}}"`. Verify with `ss -tlnp` on the host:

```bash
ssh carlos@192.168.10.10 'ss -tlnp | grep -E "LISTEN" | grep -v "127.0.0"'
```

Known ports on app-server-01 (verified with ss + curl):

| Container | Port | Verification |
|-----------|------|-------------|
| metabase | :3000 | `ss` + curl |
| open-webui | :8080 | `ss` + curl |
| phpmyadmin | :80 | `ss` (Apache) |
| adguardhome | :8083 | `ss` |
| unbound | :53 | `ss` |
| searxng | :8888 | docker ps (bridge) |
| portainer | :9443 | docker ps (bridge) |

---

## References

**Authoritative sources:**
- [`philosophy.md`](./philosophy.md) — Principles: lazy integration, fact grounding pattern
- [`architecture.md`](./architecture.md) — Package structure and lazy integration contract
- [`domain-model.md`](./domain-model.md) — Entity responsibilities (Asset/Software/Endpoint/Evidence)
- [`schema-v1.md`](./schema-v1.md) — YAML specification