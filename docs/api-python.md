# Knowledge Kernel — Python API Reference

> **Canonical reference for any developer or agent consuming the Knowledge
> Kernel from Python.**
>
> This file documents the **public contract**. Internal package layout,
> helper classes, and auxiliary fields are out of scope — they may change
> without notice.

---

## 1. Installation & Quick Start

```bash
# From the repo root (~/knowledge-kernel)
pip install -e .

# Or set a custom data directory
export CMDB_DATA_DIR=/path/to/your/entities
```

```python
from cmdb.api import cmdb_get, cmdb_exists, cmdb_list, cmdb_search

# Quick health check
health = cmdb_validate()
print(f"CMDB valid: {health['valid']}")

# Existence check (always do this before making claims)
if not cmdb_exists("my-server")["exists"]:
    print("Entity not found — search first")

# Full entity with evidence
result = cmdb_get("docker-stack-54")
if result.exists:
    ent = result.entity
    ev = result.evidence
    print(f"{ent.id} ({ent.kind}) — {ent.status}")
    print(f"Source: {ev.source_file}, observed: {ev.observed_at}")
```

---

## 2. Public API (`cmdb.api`)

All public functions are imported from `cmdb.api`. Everything else inside
the `cmdb` package is **internal** and may change.

### Query Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `cmdb_exists(entity_id)` | Fast existence check | `{"exists": bool, "entity_id": str}` |
| `cmdb_get(entity_id)` | Full entity + evidence + context | `CMDBResult` |
| `cmdb_search(query)` | Free-text search by name/desc/tags | `list[dict]` |
| `cmdb_list(kind, status, domain)` | Filtered enumeration | `list[dict]` |

### Decision Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `cmdb_assert(entity_id, must_exist, must_have_status)` | Binary gate for workflows | `{"ok": bool, "reason": str}` |
| `cmdb_impact(entity_id)` | Dependency graph before changes | `dict` |
| `cmdb_context()` | Pre-packaged agent context (call once at startup) | `dict` |

### Validation & Introspection

| Function | Purpose | Returns |
|----------|---------|---------|
| `cmdb_validate()` | Full CMDB health check | `dict` with `valid`, `errors`, `warnings`, `stats` |
| `cmdb_engine_info()` | Operational metadata (generation, hash, indexes) | `dict` |
| `cmdb_stats()` | Entity counts by kind, total relations, dataset hash | `dict` |

### Configuration

All functions accept an optional `entities_dir: Path | str` to override the
dataset location (defaults to `CMDB_DATA_DIR` env var or config default).

---

## 3. Return Types

The public API returns **composed objects**, never raw dicts. This enforces
the Kernel's core separation: **fact** ≠ **evidence** ≠ **context**.

### CMDBResult

```python
@dataclass
class CMDBResult:
    exists: bool
    entity: Optional[Entity] = None
    evidence: Optional[Evidence] = None
    context: Optional[QueryContext] = None

    # For non-existent entities
    entity_id: Optional[str] = None
    reason: Optional[str] = None
    similar_entities: List[str] = field(default_factory=list)

    def to_dict() -> dict           # New nested format
    def to_dict_legacy() -> dict    # Flat format (compat)
```

**Usage pattern:**

```python
result = cmdb_get("my-server")
if not result.exists:
    # Handle missing: result.similar_entities, result.reason
    return

ent = result.entity       # Entity object — facts only
ev = result.evidence      # Evidence object — trust metadata
ctx = result.context      # QueryContext — when/how queried

# Never: result["entity"]  (it's not a dict)
# Always: result.entity
```

### Entity

```python
@dataclass
class Entity:
    id: str
    kind: str              # asset | software | endpoint | agent | automation | procedure | project | data
    status: Optional[str]  # operational | degraded | down | deprecated
    metadata: dict         # name, description, version, tags, ports, IPs, etc.
    relations: list        # [{"type": "runs_on", "target": "..."}, ...]

    @property
    def runs_on(self) -> Optional[str]:
        """First 'runs_on' target, or None."""

    def to_dict() -> dict
```

### Evidence

```python
@dataclass
class Evidence:
    source_type: SourceType          # DECLARED | DISCOVERED | IMPORTED | INFERRED
    source_file: Optional[str]
    source_type_label: Optional[str] # "cmdb_yaml", "docker_scan", etc.

    # Temporal — CRITICAL for agent reasoning
    observed_at: str                 # ISO timestamp
    expires_at: Optional[str]
    ttl_seconds: Optional[int]

    # Lifecycle
    invalidated_at: Optional[str]
    invalidated_reason: Optional[str]

    schema_version: Optional[int]
    validated: bool
    entity_hash: Optional[str]       # SHA256[:16] for change detection

    # Confidence (evidence quality, NOT truth probability)
    confidence_level: ConfidenceLevel   # HIGH | MEDIUM | LOW | UNKNOWN
    confidence_basis: List[EvidenceBasis]

    def is_fresh() -> bool
    def age_seconds() -> float
    def time_to_expiry_seconds() -> Optional[float]
    def to_dict() -> dict
```

**Key distinction:** `confidence_level` measures **evidence quality**,
not "probability the fact is true".
- `HIGH` = multiple strong signals (schema-validated + human-declared + recent)
- `MEDIUM` = single strong or multiple weak signals
- `LOW` = weak/incomplete evidence
- `UNKNOWN` = minimal/no evidence

### QueryContext

```python
@dataclass
class QueryContext:
    queried_at: str         # ISO timestamp of this query
    cmdb_version: str       # "1.0.0"
    entities_dir: Optional[str]

    def to_dict() -> dict
```

---

## 4. Usage Examples

### Existence check before claiming

```python
from cmdb.api import cmdb_exists, cmdb_get

if not cmdb_exists("postgres-primary")["exists"]:
    # Don't hallucinate — ask or search
    results = cmdb_search("postgres")
    # Present results to user
else:
    result = cmdb_get("postgres-primary")
    if result.evidence.confidence_level == ConfidenceLevel.HIGH:
        # Safe to assert
        pass
```

### Search before assuming

```python
from cmdb.api import cmdb_search

results = cmdb_search("telegram")
for r in results[:5]:
    print(f"  {r['id']} ({r['kind']}) — score {r['score']:.2f} via {r['match_field']}")
```

### List with filters

```python
from cmdb.api import cmdb_list

# All operational software
software = cmdb_list(kind="software", status="operational")

# Everything in infrastructure domain that's down
down = cmdb_list(domain="infrastructure", status="down")
```

### Impact analysis before modification

```python
from cmdb.api import cmdb_impact

impact = cmdb_impact("docker-stack-54")
# impact["direct_dependents"], impact["transitive_dependents"], etc.
```

### Binary assertion for decision gates

```python
from cmdb.api import cmdb_assert

gate = cmdb_assert("metabase-54", must_exist=True, must_have_status="operational")
if not gate["ok"]:
    raise RuntimeError(gate["reason"])
```

### Agent startup context (single call)

```python
from cmdb.api import cmdb_context

ctx = cmdb_context()
# ctx["entities"], ctx["stats"], ctx["engine_info"]
```

---

## 5. Best Practices

1. **Always `cmdb_exists` before `cmdb_get`** — fast path, avoids exceptions.
2. **Search, don't guess IDs** — `cmdb_search` handles fuzzy matching.
3. **Read evidence, not just entity** — `evidence.confidence_level`,
   `evidence.is_fresh()`, `evidence.entity_hash` tell you whether to trust.
4. **Express uncertainty** — if `confidence_level` is `LOW` or `UNKNOWN`,
   say "unverified" or "evidence is weak", don't assert.
5. **Check freshness** — `evidence.age_seconds()` or `evidence.is_fresh()`
   before relying on operational status.
6. **Cite sources** — `evidence.source_file` and `evidence.observed_at`
   give the user an audit trail.
7. **Use `cmdb_impact` before mutating** — the Kernel doesn't mutate, but
   your code might.
8. **Never treat missing as false** — `cmdb_get("x").exists == False`
   means "not in Kernel", not "doesn't exist in reality".

---

## 6. Common Errors

| Anti-pattern | Correct approach |
|--------------|------------------|
| `result["entity"]` | `result.entity` — it's an object, not a dict |
| `result.entity.metadata.get("ip")` | `result.entity.metadata.get("ip")` ✓ but **don't infer IP from ID** (`server-192-168-1-52` ≠ IP) |
| `if not cmdb_get("x"): ...` | `if not cmdb_get("x").exists: ...` |
| `cmdb_search` returning empty → "doesn't exist" | Empty → "unverified in Kernel" |
| Treating `confidence_level` as truth probability | It's **evidence quality**. `HIGH` ≠ 100% true. |
| Hardcoding `entities_dir` in Python | Use `CMDB_DATA_DIR` env var or omit (uses config) |
| Calling `cmdb_impact` after change | Call it **before** any mutation |

---

## 7. Compatibility: `to_dict()` vs `to_dict_legacy()`

`CMDBResult` has two serialization methods:

```python
result.to_dict()         # New nested format (preferred)
# {"exists": true, "entity": {...}, "evidence": {...}, "context": {...}}

result.to_dict_legacy()  # Flat format (transition only)
# {"exists": true, "entity": {...}, "confidence": {...}, "provenance": {...}, "query_context": {...}}
```

**Rule:** New code uses `to_dict()`. `to_dict_legacy()` exists only for
transition and will be removed. Do not depend on the flat structure.

---

## 8. Stable vs. Internal

### Stable Contract (will not break without major version)

| Symbol | Type |
|--------|------|
| `cmdb_exists` | function |
| `cmdb_get` | function |
| `cmdb_search` | function |
| `cmdb_list` | function |
| `cmdb_validate` | function |
| `cmdb_impact` | function |
| `cmdb_assert` | function |
| `cmdb_context` | function |
| `cmdb_engine_info` | function |
| `cmdb_stats` | function |
| `CMDBResult` | dataclass |
| `Entity` | dataclass |
| `Evidence` | dataclass |
| `Evidence.is_fresh` | method |
| `Evidence.age_seconds` | method |
| `Evidence.time_to_expiry_seconds` | method |
| `QueryContext` | dataclass |
| `SourceType` | enum (DECLARED, DISCOVERED, IMPORTED, INFERRED) |
| `ConfidenceLevel` | enum (HIGH, MEDIUM, LOW, UNKNOWN) |
| `EvidenceBasis` | enum |

### Internal (may change)

Everything else in `cmdb.*` — `cmdb.query`, `cmdb.engine`, `cmdb.models`,
`cmdb.validator`, `cmdb.config`, `cmdb.impact`, `cmdb.rules`,
`cmdb.migrator`, internal classes, private functions.

---

## 9. Versioning

The public API follows **semantic versioning**. Breaking changes only in
major versions. The current frozen surface is **v1.0.0** (Kernel L2.1).

Check `cmdb_engine_info()["generation"]` and `cmdb_engine_info()["dataset_hash"]`
at runtime to verify which dataset your code is querying.