# Hermes Tools for Agent-CMDB

Tool wrappers exposing Agent-CMDB functionality to Hermes Agent.

## Storage Location

**Default:** `~/knowledge/knowledge-kernel/`

Override with env var `CMDB_DATA_DIR=/path/to/dataset`.

Tools read from and write to the configured dataset.

## Available Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cmdb_exists(entity_id)` | Check existence | Before ANY factual claim |
| `cmdb_get(entity_id)` | Get full entity + evidence | Deep reasoning about entity |
| `cmdb_assert(entity_id, kind, status)` | Binary validation | Decision requires specific state |
| `cmdb_impact(entity_id)` | Dependency analysis | BEFORE modifying infrastructure |
| `cmdb_context(agent_id)` | Pre-packaged context | Agent startup (call once) |
| `cmdb_reload()` | Reload derived indexes | After editing YAML files directly |

## Import Pattern

```python
from tools.cmdb_exists import cmdb_exists
from tools.cmdb_get import cmdb_get
from tools.cmdb_assert import cmdb_assert
from tools.cmdb_impact import cmdb_impact
from tools.cmdb_context import cmdb_context
from tools.cmdb_reload import cmdb_reload
```

## Tool Registration (config.yaml)

```yaml
tools:
  - name: cmdb_exists
    description: Check if entity exists in Agent-CMDB
    function: tools.cmdb_exists:cmdb_exists
    
  - name: cmdb_get
    description: Get entity with facts + evidence
    function: tools.cmdb_get:cmdb_get
    
  - name: cmdb_assert
    description: Assert entity exists with expected properties
    function: tools.cmdb_assert:cmdb_assert
    
  - name: cmdb_impact
    description: Analyze impact before modifying infrastructure
    function: tools.cmdb_impact:cmdb_impact
    
  - name: cmdb_context
    description: Get pre-packaged context for agent (call at startup)
    function: tools.cmdb_context:cmdb_context
    
  - name: cmdb_reload
    description: Reload derived indexes after editing YAML
    function: tools.cmdb_reload:cmdb_reload
```

## Testing

Tests live at the repo root (`~/agent-cmdb/tests/`) — they cover the core API plus all tools. There are no separate integration tests in `integrations/hermes/tests/`; the root suite is the source of truth.

```bash
cd ~/agent-cmdb
CMDB_DATA_DIR=~/knowledge/knowledge-kernel pytest tests/ -v
```