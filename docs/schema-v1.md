# Schema v1 — knowledge-kernel Entity Specification

**Status:** Stable (v1.2)
**Compatibility:** Schema is frozen. Dataset may grow; format does not change.

---

## 1. Design Principles (non-negotiable)

These principles define the Kernel's identity:

1. **Facts are immutable until replaced.**
   A fact in the Kernel is correct until it is replaced by a newer, verified fact.

2. **Every assertion must be backed by evidence.**
   If the Kernel does not contain a fact, the agent treats it as unverified.

3. **Freshness is computed, never stored.**
   `expires_at` is derived from `observed_at + domain TTL`. No stale values can accumulate.

4. **Relations always point to entities.**
   A relation `target` is always an `id` in the Kernel — never a literal IP, hostname, or URL.

5. **The Kernel never reasons or decides.**
   It answers three questions: *"Does it exist?"* / *"What depends on it?"* / *"Is it fresh?"* — nothing more.

---

## 2. Base envelope (required)

Every entity **must** have this minimum structure:

```yaml
schema_version: 1

id: <unique-identifier>       # stable identity
kind: <entity-kind>            # asset | software | endpoint | automation | data
domain: <domain>               # infrastructure | automation | knowledge | organization
metadata:
  name: <human-readable-name>
  description: <optional-description>

status: <operational-status>

relations:
  - type: <relation-type>
    target: <target-entity-id>

evidence:
  source_file: <path>
  confidence_level: <HIGH | MEDIUM | LOW | UNKNOWN>
  confidence_basis: [<SCHEMA_VALIDATED | HUMAN_DECLARED | RUNTIME_CHECKED | INFERRED | DISCOVERED>]
  observed_at: <ISO-8601-timestamp>

criticality:
  business: <low | medium | high>
  operational: <low | medium | high>
  technical: <low | medium | high>

tags:
  - <tag>
```

### Complete example — Software

```yaml
schema_version: 1

id: ollama
kind: software
domain: infrastructure

metadata:
  name: Ollama
  description: Local LLM inference server
  version: "0.5"

status: operational

relations:
  - type: runs_on
    target: orange-pi-54
  - type: exposes
    target: ollama-api

evidence:
  source_file: software/ollama.yaml
  confidence_level: HIGH
  confidence_basis: [SCHEMA_VALIDATED, HUMAN_DECLARED]
  observed_at: "2026-07-07T00:00:00Z"

criticality:
  business: medium
  operational: high
  technical: low

tags:
  - llm
  - inference
```

### Complete example — Endpoint

```yaml
schema_version: 1

id: ollama-api
kind: endpoint
domain: infrastructure

metadata:
  name: Ollama API
  # IDENTITY: host/port/protocol may change without changing the ID
  host: 192.168.1.54
  port: 11434
  protocol: http

status: operational

relations:
  - type: exposed_by
    target: ollama

evidence:
  source_file: endpoint/ollama-api.yaml
  confidence_level: HIGH
  confidence_basis: [SCHEMA_VALIDATED, RUNTIME_CHECKED]
  observed_at: "2026-07-07T00:00:00Z"

tags:
  - llm
  - api
```

---

## 3. Identity vs Metadata

| Field | Type | Immutable | Description |
|-------|------|-----------|-------------|
| `schema_version` | `integer` | N/A | Always `1` for v1 |
| `id` | `string` | ✅ Yes | Primary key — never changes |
| `kind` | `string` | ❌ No | Can change if reclassified |
| `domain` | `string` | ❌ No | Can change as understanding evolves |

**Rule:** `id` is the primary key. It is never modified, reused, or deleted. Mark `status: deprecated` instead.

### What is NOT identity

Fields in `metadata` are **observed facts** — they describe the current state, not the permanent identity:

```yaml
# host/port/protocol are observed — they may change
metadata:
  host: 192.168.1.54    # could become ollama.internal
  port: 11434           # could become 443
  protocol: http        # could become https
```

This is intentional. An endpoint's **ID is its communication identity** — stable regardless of how the connection details evolve.

---

## 4. Valid `kind` catalog (closed)

| Kind | Description | Example |
|------|-------------|---------|
| `asset` | Physical or virtual host | `orange-pi-54`, `servidor-pos` |
| `software` | Executing process or service | `ollama`, `mysql`, `hermes` |
| `endpoint` | Observable communication identity | `ollama-api`, `telegram-bot` |
| `automation` | Scheduled scripts, jobs, pipelines | `sync-firebird-mysql` |
| `data` | Databases, backups, datasets | `firebird_db`, `backup-20260621` |

**Rule:** Do not add new `kind` without a justified operational use case.

---

## 5. Typed relations catalog (closed + extends)

### Format

```yaml
relations:
  - type: <relation-type>
    target: <target-entity-id>    # always an entity ID — never a literal
```

### Relation reference

| Relation | Target must be | Description | Transitive |
|----------|----------------|-------------|------------|
| `runs_on` | `asset` | Host where software executes | ❌ No |
| `exposes` | `endpoint` | Software exposes this endpoint | ❌ No |
| `exposed_by` | `software` | Endpoint belongs to this software | ❌ No |
| `uses` | Any kind | Functional dependency | ✅ Yes |
| `reads` | `data`, `software` | Reads data | ✅ Yes |
| `writes` | `data`, `software` | Writes data | ✅ Yes |
| `calls` | `endpoint`, `software` | HTTP/RPC invocation | ❌ No |
| `owns` | Any kind | Ownership / operational responsibility | ❌ No |
| `backs_up` | `data` | Backup / replication | ❌ No |
| `monitors` | Any kind | Monitoring / health checks | ❌ No |

### Validity rules

| Rule | Validation |
|------|------------|
| `target` must exist | `cmdb_validate()` rejects unknown targets |
| `type` must be in catalog | Unknown types rejected |
| `runs_on` only to `asset` | Validator rejects `runs_on` to non-asset |
| No duplicates | Same `type + target` once per entity |
| `exposes` only to `endpoint` | Validator enforces endpoint target |

### `runs_on` is computed — not stored separately

```python
entity = cmdb_get("ollama")
entity.runs_on   # → "orange-pi-54" — computed from relations
                # NOT from metadata.runs_on
```

The Kernel traverses the `relations` list at query time and returns the `target` of the first `runs_on` relation.

---

## 6. Evidence structure

The `evidence` block answers: *"Why do we believe this?"*

```yaml
evidence:
  source_file: software/ollama.yaml
  confidence_level: HIGH
  confidence_basis:
    - SCHEMA_VALIDATED      # passed YAML schema validation
    - HUMAN_DECLARED        # intentionally declared by a human
  observed_at: "2026-07-07T00:00:00Z"
```

### Confidence levels

| Level | Meaning | When used |
|-------|---------|-----------|
| `HIGH` | Multiple strong signals | Schema validated + human declared + recent |
| `MEDIUM` | Single strong signal | Schema validated OR human declared |
| `LOW` | Weak or incomplete evidence | Auto-discovered, no validation |
| `UNKNOWN` | Minimal or no evidence | Unknown origin |

### Confidence basis

| Basis | Description |
|-------|-------------|
| `SCHEMA_VALIDATED` | Passed YAML schema validation |
| `HUMAN_DECLARED` | Intentionally declared by a human |
| `RUNTIME_CHECKED` | Verified at runtime (health check, SSH scan) |
| `INFERRED` | Deduced from other facts |
| `DISCOVERED` | Auto-discovered by scanner |

### Freshness — computed, never stored

```yaml
evidence:
  observed_at: "2026-07-07T00:00:00Z"   # recorded when verified
```

`expires_at` is **derived** from `observed_at + domain TTL` at query time:

| Domain | Default TTL |
|--------|-------------|
| Infrastructure | 1 hour |
| Endpoints | 5–15 minutes |
| Software | 24 hours |
| Policies | 30 days |
| Procedures | 90 days |

The Kernel never stores `expires_at` — it would go stale. Freshness is always computed.

---

## 7. Operational status

| Status | Description | When to use |
|--------|-------------|-------------|
| `operational` | Normal operation | Default state |
| `degraded` | Operating with limitations | Reduced performance, fallback active |
| `down` | Out of service | Total failure, scheduled maintenance |
| `deprecated` | Scheduled for removal | In retirement — no new dependencies |

**Rule:** Entities with `status: deprecated` must not acquire new incoming relations.

---

## 8. Schema validation rules

### ID format

| Rule | Pattern | Example ✅ | Example ❌ |
|------|---------|------------|------------|
| Unique across entire CMDB | — | `mysql`, `orange-pi-54` | Duplicated ID |
| Lowercase | `^[a-z0-9-]+$` | `server-54`, `firebird-db` | `Server-54`, `FirebirdDB` |
| Kebab-case | No underscores | `backup-nightly` | `backup_nightly` |
| Max 64 chars | `len(id) ≤ 64` | — | `sync-firebird-mysql-backup-verification...` |

### Relations

| Rule | Check |
|------|-------|
| `target` exists | ID must be in the Kernel |
| `type` is in catalog | Only relations from section 5 |
| `runs_on` → `asset` only | Validator rejects otherwise |
| No duplicate `type + target` | One relation per type-target pair |

### Evidence

| Rule | Check |
|------|-------|
| `observed_at` is ISO-8601 | Parseable by `datetime.fromisoformat()` |
| `confidence_level` is valid enum | One of HIGH/MEDIUM/LOW/UNKNOWN |
| `confidence_basis` values are valid | Each in [SCHEMA_VALIDATED, HUMAN_DECLARED, RUNTIME_CHECKED, INFERRED, DISCOVERED] |

---

## 9. Validation checklist (pre-commit)

Before pushing a change to the Kernel:

- [ ] `schema_version: 1` present
- [ ] `id` unique, lowercase, kebab-case, ≤64 chars
- [ ] `kind` in [asset, software, endpoint, automation, data]
- [ ] `metadata.name` present
- [ ] `status` is valid value
- [ ] All `relations[].type` in catalog
- [ ] All `relations[].target` exist in Kernel
- [ ] `runs_on` targets are `kind: asset`
- [ ] `exposes` targets are `kind: endpoint`
- [ ] `evidence.observed_at` is ISO-8601
- [ ] `evidence.confidence_level` is valid enum
- [ ] `criticality` (if declared) has all three fields
- [ ] `cmdb_validate()` passes without errors

---

## Change history

| Date | Version | Change |
|------|---------|--------|
| 2026-06-22 | draft | Initial schema — Registry era |
| 2026-07-07 | v1.2 | Complete rewrite: English, exposes/exposed_by, endpoint identity vs observation, `entity.runs_on` computed, freshness as derived property, principles as contract |

---

## References

**Authoritative sources:**
- [`philosophy.md`](./philosophy.md) — Principles: schema validity, relations, freshness
- [`architecture.md`](./architecture.md) — Package structure and lazy integration
- [`domain-model.md`](./domain-model.md) — Entity responsibilities

**Related:**
- [`usage-patterns.md`](./usage-patterns.md) — Query patterns