# Failure Modes — knowledge-kernel

**Purpose:** Document recurring failure patterns and their corrections. This is not a log — it is a catalog.

---

## 1. Knowledge vs Inference

### Error: Storing inference in metadata

**Symptom:**
```python
# ❌ WRONG — metadata.host should come from observation, not inference
metadata:
  runs_on: server-53     # inferred from training data
  inferred_from: "LLM memory"
```

**Correction:**
```python
# ✅ RIGHT — runs_on is computed from relations at query time
entity.runs_on   # → "app-server-01" — from relations[], not metadata
```

**Rule:** `metadata.runs_on` does not exist. Use the `runs_on` relation and call `entity.runs_on`.

---

## 2. Relations Pointing to Literals

### Error: `target` as a literal IP or hostname

**Symptom:**
```yaml
# ❌ WRONG — target must be an entity ID
relations:
  - type: runs_on
    target: 192.168.10.10     # literal IP — not an entity
```

**Correction:**
```yaml
# ✅ RIGHT — target is an entity ID
relations:
  - type: runs_on
    target: app-server-01      # asset entity
```

**Rule:** Relations always point to entity IDs. Never literals.

---

## 3. Endpoint as URL

### Error: Storing full URL in metadata without separating identity

**Symptom:**
```yaml
# ❌ WRONG — mixes identity (name) with observation (connection details)
id: ollama-api
metadata:
  url: http://192.168.10.10:11434
```

**Correction:**
```yaml
# ✅ RIGHT — ID is stable identity; host/port/protocol are observed facts
id: ollama-api
kind: endpoint
metadata:
  host: 192.168.10.10    # observed — may change
  port: 11434           # observed — may change
  protocol: http       # observed — may change
```

**Rule:** An endpoint ID is its **communication identity**. Tomorrow it can be `https://ollama.internal:443` and still be `ollama-api`.

---

## 4. Stale Examples in Documentation

### Error: Using obsolete entity names or IPs

**Symptom:**
```python
# ❌ WRONG — references old Infrastructure
entity.runs_on  # → server-53 (doesn't exist)
cmdb_get("server-52")  # doesn't exist
```

**Correction:**
```python
# ✅ RIGHT — use current entity IDs
cmdb_get("ollama").entity.runs_on  # → app-server-01
cmdb_get("app-server-01")           # current asset
```

**Rule:** Always use entity IDs verified against the current Kernel.

---

## 5. `runs_on` vs `uses` Confusion

### Error: Putting a dependency in `runs_on`

**Symptom:**
```yaml
# ❌ WRONG — docker is software, not the host
relations:
  - type: runs_on
    target: docker       # docker is not a host
```

**Correction:**
```yaml
# ✅ RIGHT — docker is a dependency (software), not the host
relations:
  - type: runs_on
    target: app-server-01     # physical host
  - type: uses
    target: docker          # software dependency
```

**Rule:** `runs_on` always points to `kind: asset`. Use `uses` for software dependencies.

---

## 6. Database as runs_on Target

### Error: DB is not a host

**Symptom:**
```yaml
# ❌ WRONG — MySQL is software, not a host
relations:
  - type: runs_on
    target: mysql
```

**Correction:**
```yaml
# ✅ RIGHT — database runs on an asset, depends on MySQL
relations:
  - type: runs_on
    target: app-server-01
  - type: uses
    target: mysql
```

**Rule:** Databases are `kind: data` or `kind: software`. They execute on hosts via `runs_on`, not as hosts.

---

## 7. Confusing `depends_on` with `runs_on`

### Error: Using generic `depends_on` relation

**Symptom:**
```yaml
# ❌ WRONG — old Registry format
depends_on:
  - mysql
  - ollama
```

**Correction:**
```yaml
# ✅ RIGHT — typed relations with semantic meaning
relations:
  - type: uses
    target: mysql
  - type: uses
    target: ollama
```

**Rule:** Always use typed relations. `runs_on` is physical location (1-hop, not transitive). `uses` is functional dependency (BFS, transitive).

---

## 8. Missing Evidence Block

### Error: Entity without `evidence` field

**Symptom:**
```yaml
# ❌ WRONG — no evidence means unverified
id: ollama
kind: software
# no evidence block
```

**Correction:**
```yaml
# ✅ RIGHT — evidence proves this fact is verified
evidence:
  source_file: software/ollama.yaml
  confidence_level: HIGH
  confidence_basis: [SCHEMA_VALIDATED, HUMAN_DECLARED]
  observed_at: "2026-07-07T00:00:00Z"
```

**Rule:** Every entity must have an `evidence` block. If it doesn't, the agent must treat it as UNKNOWN confidence.

---

## 9. Storing `expires_at`

### Error: Manually setting expiration date

**Symptom:**
```yaml
# ❌ WRONG — expires_at would go stale
evidence:
  observed_at: "2026-07-07T00:00:00Z"
  expires_at: "2026-07-08T00:00:00Z"    # manually set — will be wrong
```

**Correction:**
```yaml
# ✅ RIGHT — freshness is derived at query time
evidence:
  observed_at: "2026-07-07T00:00:00Z"
  # expires_at is computed: observed_at + domain TTL
```

**Rule:** `expires_at` is never stored. Always computed from `observed_at + domain TTL`.

---

## 10. Duplicate Entity IDs

### Error: Same ID in different kind folders

**Symptom:**
```
software/metabase.yaml   → id: metabase
endpoint/metabase.yaml   → id: metabase   # conflict!
```

**Correction:**
```yaml
# Use distinct IDs that reflect the entity role
software/metabase.yaml       → id: metabase
endpoint/metabase-ui.yaml    → id: metabase-ui
```

**Rule:** IDs must be unique across the entire Kernel. Use suffixes for endpoint variants.

---

## 11. Assuming Localhost for Remote Services

### Error: Using localhost in network fields

**Symptom:**
```yaml
# ❌ WRONG — ollama runs on app-server-01, not local
metadata:
  network:
    host: localhost
    port: 11434
```

**Correction:**
```yaml
# ✅ RIGHT — host is the asset where the service runs
relations:
  - type: runs_on
    target: app-server-01
# host comes from the asset's metadata
```

**Rule:** Never use `localhost` for services running on remote assets. Query `cmdb_get(asset_id)` for the real host.

---

## 12. Not Checking `cmdb_validate()` Before Push

### Error: Pushing YAML with broken relations

**Symptom:** `cmdb_validate()` returns errors after commit.

**Correction:**
```bash
# Always run before commit
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 -c "
from cmdb.api import cmdb_validate
v = cmdb_validate()
assert v['valid'], f'Validation failed: {v[\"errors\"]}'
print('✅ cmdb_validate passed')
"
```

---

## 13. `REVERSE_DEPENDENCY_RELATIONS` Defined But Unused

### Error: Declaring reverse relations but not implementing the logic

**Symptom:** `REVERSE_DEPENDENCY_RELATIONS` in code but `_find_dependents` only checks `DEPENDENCY_RELATIONS`.

**Correction:** The reverse relations (`exposed_by`, `hosts`) are handled by computing them from the graph. The Kernel traverses relations in both directions by checking if `target → current_id` with relation type in `DEPENDENCY_RELATIONS`.

**Rule:** Always verify that declared constants are actually used in the logic.

---

## Change history

| Date | Version | Change |
|------|---------|--------|
| 2026-07-07 | v1.2 | Full rewrite: Registry-era patterns removed, all references updated to cmdb API, entity.runs_on, endpoint identity, freshness as derived |

---

## References

**Authoritative sources:**
- [`domain-model.md`](./domain-model.md) — Entity responsibilities, identity vs observation
- [`schema-v1.md`](./schema-v1.md) — Schema validation rules

**Related:**
- [`philosophy.md`](./philosophy.md) — Principles: identity, immutability, evidence