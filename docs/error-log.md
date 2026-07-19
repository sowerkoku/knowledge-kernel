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

## 14. Bare ISO Dates in YAML Breaking `json.dumps` in Hash Computation

### Error: `TypeError: Object of type date is not JSON serializable`

**Symptom:** `kpi.py` crashes with `TypeError` on `hermes-gateway-53.yaml`. Any call to `cmdb_get()` on entities with bare (unquoted) ISO dates in `metadata.*` fields crashes at hash computation.

**Root cause:** PyYAML parses unquoted ISO-8601 dates as `datetime.date` objects. `_compute_entity_hash()` calls `json.dumps(stable)` with no `default` handler. When `metadata` contains a bare date field (e.g., `started: 2026-07-06`), `json.dumps` raises `TypeError`.

**Affected entity:** `hermes-gateway-53` has `metadata.started: 2026-07-06`.

**Fix:** Added `_json_default()` serializer in `cmdb/query.py`:

```python
def _json_default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

serialized = json.dumps(stable, sort_keys=True, default=_json_default)
```

**Commit:** `c956cfe` — `fix(query): serialize date/datetime in entity hash`

---

## 15. Skill ↔ Repo Drift (`~/.hermes/skills/` vs `integrations/hermes/`)

### Error: `test_skill_two_copies_remain_in_sync` fails after non-git tool writes

**Symptom:** `pytest tests/test_doc_governance.py::test_skill_two_copies_remain_in_sync` fails — SKILL.md bytes differ between `~/.hermes/skills/knowledge-kernel/` (11505 bytes) and `~/knowledge-kernel/integrations/hermes/` (11359 bytes).

**Root cause:** The `~/.hermes/skills/` directory has no git tracking. When a non-git tool (Hermes internal process, cron job, external script) regenerates `SKILL.md` without going through the git sync workflow, the skill copy diverges from the repo.

**Evidence:**
```
skill:  11505 bytes, modified 2026-07-18 21:23
repo:   11359 bytes, modified 2026-07-16 21:44
sha256 mismatch: ebef82... vs fe1738...
Drift content: duplicate `scripts/` line + spurious `bugfix-datetime-serialization.md` reference
```

**Direction of truth:** `~/knowledge-kernel/integrations/hermes/SKILL.md` is the git-tracked canonical source. `~/.hermes/skills/` is a working copy that must be synced FROM the repo, never the other way around.

**Fix:** Copy repo → skill and commit the sync:
```bash
cp ~/knowledge-kernel/integrations/hermes/SKILL.md ~/.hermes/skills/knowledge-kernel/
```

**Same drift applies to tools/**: Copy repo → skill to ensure consistency.
```bash
cp ~/knowledge-kernel/integrations/hermes/tools/*.py ~/.hermes/skills/knowledge-kernel/tools/
```

**Prevention:** The `test_skill_two_copies_remain_in_sync` test already guards this. Any drift = test failure. Maintainers must run `pytest tests/` before push.

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