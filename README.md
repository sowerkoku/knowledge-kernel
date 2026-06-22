# Agent CMDB

**Configuration Management Database for AI Agent Ecosystems**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What is Agent CMDB?

Agent CMDB is a **configuration management database** designed for AI agent ecosystems. It provides:

- **Entity inventory** — Track agents, software, assets, data, and automation
- **Dependency graph** — Typed relations (`runs_on`, `uses`, `reads`, `writes`)
- **Impact analysis** — Answer: "What breaks if X fails?"
- **Schema validation** —catch inconsistencies before they cause outages

Think **NetBox for AI infrastructure** — not a skill registry, but a living map of your agent ecosystem.

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/sowerkoku/agent-cmdb.git
cd agent-cmdb

# Add to PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$PWD"
```

### Validate your CMDB

```python
from cmdb.validator import cmdb_validate
from pathlib import Path

# Validate entities in /path/to/entities
result = cmdb_validate(Path("/path/to/entities"))

if result["valid"]:
    print(f"✅ CMDB valid: {result['stats']['total']} entities")
else:
    print(f"❌ {len(result['errors'])} errors:")
    for err in result["errors"]:
        print(f"  - {err['entity_id']}.{err['field']}: {err['message']}")
```

### Run migration (v0 → v1)

```bash
# Dry-run first
python -m cmdb.migrator --dry-run --entities-dir /path/to/entities

# Review migration-plan.md, then apply
python -m cmdb.migrator --apply --entities-dir /path/to/entities
```

---

## Schema v1

Entities use YAML format with schema v1:

```yaml
schema_version: 1

id: web-server
kind: software

metadata:
  name: Example Web Server
  description: nginx web server
  version: "1.24"

status: operational

relations:
  - type: runs_on
    target: app-server-01
  - type: uses
    target: postgres-db

criticality:
  business: medium
  operational: high
  technical: low
```

### Entity kinds

| Kind | Description | Example |
|------|-------------|---------|
| `asset` | Physical or virtual hardware | `server-01`, `router-core` |
| `software` | Services, daemons, CLIs | `nginx`, `mysql`, `ollama` |
| `automation` | Scripts, jobs, pipelines | `backup-nightly`, `sync-firebird` |
| `data` | Databases, backups, datasets | `production-db`, `backup-archive` |
| `endpoint` | URLs, HTTP interfaces | `api.telegram.org`, `ollama:11434` |

### Relation types

| Relation | Semantic | Transitiva | Example |
|----------|----------|------------|---------|
| `runs_on` | Host location | ❌ No | `nginx` runs_on `server-01` |
| `uses` | Functional dependency | ✅ Sí | `hermes` uses `ollama` |
| `reads` | Data read | ✅ Sí | `sync` reads `firebird_db` |
| `writes` | Data write | ✅ Sí | `sync` writes `mysql_cic` |
| `calls` | HTTP/RPC invocation | ❌ No | `automation` calls `webhook` |
| `owns` | Ownership/governance | ❌ No | `team-infra` owns `server-01` |
| `backs_up` | Backup/replication | ❌ No | `backup-job` backs_up `production-db` |
| `monitors` | Health checks/alerts | ❌ No | `watchdog` monitors `ollama` |

---

## Impact Analysis (Coming Soon)

```python
from cmdb.query import cmdb_impact

# What breaks if Ollama fails?
impact = cmdb_impact("ollama")

print(f"Agents affected: {impact['agents']}")
print(f"Software affected: {impact['software']}")
print(f"Automation affected: {impact['automation']}")
```

---

## Project Structure

```
agent-cmdb/
├── cmdb/
│   ├── validator.py       # Schema validation
│   ├── migrator.py        # v0 → v1 migration
│   └── rules/             # Validation rules (modular)
│       ├── schema.py
│       ├── identity.py
│       ├── relations.py
│       └── lifecycle.py
├── docs/
│   ├── domain-model.md    # Semantic contract (Impact First)
│   └── schema-v1.md       # Technical specification
├── examples/              # Sanitized example entities
├── tests/                 # Test suite
├── README.md
├── LICENSE
└── pyproject.toml
```

---

## Design Principles

### Impact First

> Every entity must justify a query or impact analysis that cannot be resolved without it.

If an entity doesn't enable operational queries or impact analysis, it's configuration — not an entity.

### Facts vs Narrative

- **Facts** (YAML) — Indexable, queryable, versioned
- **Narrative** (docs/) — Context, patterns, runbooks

Never mix them in the same file.

### Conservative Inference

- Kind inferred from folder structure (with manual override)
- Unknown status → error (no guessing)
- Missing relation targets → warning (not auto-created)

---

## Migration from v0

If you have existing entities in legacy format:

```bash
# 1. Review current state
python -m cmdb.migrator --dry-run

# 2. Review migration-plan.md

# 3. Apply (creates backup automatically)
python -m cmdb.migrator --apply
```

**Backup location:** `./registry-v0-backup-YYYYMMDD-HHMMSS/`

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/impact-analysis`)
3. Add tests for new features
4. Ensure `cmdb_validate()` passes on examples
5. Submit a pull request

---

## Roadmap

### Q3 2026

- [x] Schema v1 specification
- [x] Validator with modular rules
- [x] Migration tooling (v0 → v1)
- [ ] `cmdb_impact()` implementation
- [ ] CLI: `cmdb graph`, `cmdb diagram`
- [ ] Auto-discovery: `cmdb discover docker`, `cmdb discover hermes`

### Future

- [ ] `agent` as separate kind (currently `software`)
- [ ] Web UI for browsing entities
- [ ] Integration with observability stacks (Prometheus, Grafana)
- [ ] Conflict detection (multiple entities claiming same relation)