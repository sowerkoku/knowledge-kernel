# Audit Methodology — knowledge-kernel Knowledge Kernel

**Purpose:** How to audit the Kernel — validate integrity, measure coverage, detect staleness.

**State:** Audits the Kernel, not the underlying infrastructure. Compare Kernel state against reality separately.

---

## 1. cmdb_validate() — Structural Integrity

Always start here. This is the Kernel's self-check:

```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 -c "
from cmdb.api import cmdb_validate
v = cmdb_validate()
print(f'Valid: {v[\"valid\"]}')
print(f'Total entities: {v[\"stats\"][\"total\"]}')
print(f'By kind: {v[\"stats\"][\"by_kind\"]}')
if v['errors']: print(f'ERRORS: {v[\"errors\"]}')
if v['warnings']: print(f'Warnings: {len(v[\"warnings\"])}')
"
```

`cmdb_validate()` checks:
- YAML schema validity
- Broken relations (target doesn't exist)
- Duplicate IDs
- Orphan endpoints (endpoint with no `exposed_by` relation)
- Missing required fields (id, kind, metadata.name, evidence)

---

## 2. Relation Integrity Audit

Check for broken relations — relations that point to non-existent entities:

```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 -c "
from cmdb.api import cmdb_list, cmdb_validate

# Check each entity's relations
for e in cmdb_list():
    for rel in e.get('relations', []):
        target = rel['target']
        # Check if target exists
        exists = any(x['id'] == target for x in cmdb_list())
        if not exists:
            print(f'BROKEN: {e[\"id\"]} --[{rel[\"type\"]}]--> {target}')
"
```

---

## 3. Stale Evidence Audit

Which entities have evidence older than their domain TTL?

```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 -c "
from cmdb.api import cmdb_list, cmdb_get
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
for e in cmdb_list(domain='infrastructure'):
    fact = cmdb_get(e['id'])
    if not fact.evidence.is_fresh():
        ttl_remaining = fact.evidence.time_to_expiry_seconds()
        print(f'STALE: {e[\"id\"]} ({ttl_remaining}s ago)')
"
```

---

## 4. Fact Coverage Audit

Can the Kernel answer the key operational questions?

| Question | Kernel answer requires |
|----------|----------------------|
| "Where does X run?" | `kind: software` with `runs_on` relation |
| "What runs here?" | `kind: asset` with dependents via `runs_on` |
| "How to reach X?" | `kind: endpoint` with `host/port/protocol` in metadata |
| "What breaks if X fails?" | `cmdb_impact(X)` with `depends_on_me` |
| "What does X depend on?" | `cmdb_impact(X)` with `depends_on` |

```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 -c "
from cmdb.api import cmdb_list, cmdb_get

# Check: all software should have runs_on
software = cmdb_list(kind='software')
missing_runs_on = [e['id'] for e in software
                   if not any(r['type'] == 'runs_on' for r in e.get('relations', []))]
print(f'Software missing runs_on: {missing_runs_on}')

# Check: all endpoints should have exposed_by
endpoints = cmdb_list(kind='endpoint')
missing_exposed_by = [e['id'] for e in endpoints
                       if not any(r['type'] == 'exposed_by' for r in e.get('relations', []))]
print(f'Endpoints missing exposed_by: {missing_exposed_by}')

# Check: all assets should have at least one software running on them
assets = cmdb_list(kind='asset')
for a in assets:
    deps = cmdb_impact(a['id'])['depends_on_me']['direct']
    has_software = any(d['kind'] == 'software' for d in deps)
    if not has_software:
        print(f'Asset {a[\"id\"]} has no software running on it')
"
```

---

## 5. Endpoint Audit

Endpoints should have host/port/protocol in metadata:

```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 -c "
from cmdb.api import cmdb_list

for e in cmdb_list(kind='endpoint'):
    m = e.get('metadata', {})
    missing = [f for f in ['host', 'port', 'protocol'] if f not in m]
    if missing:
        print(f'ENDPOINT INCOMPLETE: {e[\"id\"]} missing {missing}')
"
```

---

## 6. Impact Graph Audit

Verify the impact graph is connected — no orphaned clusters:

```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 -c "
from cmdb.api import cmdb_list, cmdb_impact

# Every entity should appear in at least one impact chain
all_ids = {e['id'] for e in cmdb_list()}

connected = set()
for e in cmdb_list():
    impact = cmdb_impact(e['id'])
    for cat in ['depends_on', 'depends_on_me']:
        for level in ['direct', 'transitive']:
            for d in impact.get(cat, {}).get(level, []):
                connected.add(d['id'])
                connected.add(e['id'])

orphans = all_ids - connected
if orphans:
    print(f'ORPHAN ENTITIES (no impact relations): {orphans}')
else:
    print('All entities participate in at least one impact relation')
"
```

---

## 7. Critical Entity Audit

Check that all HIGH-criticality entities have:
- Evidence with HIGH confidence
- No broken relations
- At least one way to recover (backup, redundancy)

```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 -c "
from cmdb.api import cmdb_list, cmdb_get

for e in cmdb_list():
    crit = e.get('criticality', {})
    if crit.get('business') == 'high':
        fact = cmdb_get(e['id'])
        issues = []
        if fact.evidence.confidence_level != 'HIGH':
            issues.append(f'confidence={fact.evidence.confidence_level}')
        if e.get('status') == 'down':
            issues.append('status=down')
        if not any(r['type'] in ('backs_up', 'runs_on') for r in e.get('relations', [])):
            if e.get('kind') == 'data':
                issues.append('no backup relation')
        if issues:
            print(f'CRITICAL WARNING {e[\"id\"]}: {\" | \".join(issues)}')
"
```

---

## 8. Dataset vs Reality (External Audit)

The Kernel audits itself. Validating Kernel vs real infrastructure requires separate tooling:

```bash
# Kernel says: ollama runs on orange-pi-54, exposes ollama-api
# Reality check via SSH:
ssh carlos@192.168.1.54 'ss -tlnp | grep 11434'
ssh carlos@192.168.1.54 'curl -s http://localhost:11434/api/tags'
```

This is the job of the **Runtime Discovery skill** — not part of the Kernel itself.

---

## 9. Coverage KPIs

Measure what percentage of real infrastructure is captured in the Kernel:

| Category | Metric | How to measure |
|----------|--------|----------------|
| **Entity coverage** | % of real entities in Kernel | Compare cmdb_list() against discovered reality |
| **Relation coverage** | % of relations modeled | cmdb_impact() returns populated graphs |
| **Evidence freshness** | % of facts within TTL | Count stale vs fresh via is_fresh() |
| **Confidence quality** | % of entities with HIGH confidence | cmdb_validate() stats |

---

## Change history

| Date | Version | Change |
|------|---------|--------|
| 2026-06-22 | draft | Initial 9-level audit for Registry era |
| 2026-07-07 | v1.2 | Complete rewrite for Knowledge Kernel: cmdb_validate(), entity.runs_on, exposes/exposed_by, freshness audit, coverage KPIs |

---

## References

**Authoritative sources:**
- [`architecture.md`](./architecture.md) — How the audit integrates with the cmdb_validate API
- [`governance.md`](./governance.md) — What earns audit attention (HIGH-criticality, stale evidence)

**Related:**
- [`domain-model.md`](./domain-model.md) — Entity responsibilities
- [`schema-v1.md`](./schema-v1.md) — Schema validation rules