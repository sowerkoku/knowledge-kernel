# knowledge-kernel — Examples

Sanitized example entities for documentation and testing.

These entities demonstrate schema v1 format without revealing production infrastructure details.

## Usage

```python
from cmdb.validator import cmdb_validate
from pathlib import Path

# Validate examples
result = cmdb_validate(Path("examples"))
assert result["valid"], result["errors"]
```

## Entity examples

### software/web-server.yaml

```yaml
schema_version: 1
id: web-server
kind: software

metadata:
  name: Example Web Server
  description: nginx web server for demonstration
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

### asset/app-server-01.yaml

```yaml
schema_version: 1
id: app-server-01
kind: asset

metadata:
  name: Application Server 01
  description: Virtual machine for application hosting
  specs:
    cpu: 4 vCPU
    ram: 16 GB
    disk: 200 GB SSD

status: operational

criticality:
  business: high
  operational: high
  technical: medium
```

### data/postgres-db.yaml

```yaml
schema_version: 1
id: postgres-db
kind: data

metadata:
  name: PostgreSQL Database
  description: Main application database
  engine: PostgreSQL 15
  size: "5 GB"

status: operational

relations:
  - type: runs_on
    target: db-server-01
  - type: backs_up
    target: nightly-backup

criticality:
  business: high
  operational: high
  technical: high
```

### automation/nightly-backup.yaml

```yaml
schema_version: 1
id: nightly-backup
kind: automation

metadata:
  name: Nightly Backup Job
  description: Automated backup pipeline
  schedule: "0 2 * * *"

status: operational

relations:
  - type: reads
    target: postgres-db
  - type: writes
    target: backup-storage

criticality:
  business: high
  operational: medium
  technical: medium
```