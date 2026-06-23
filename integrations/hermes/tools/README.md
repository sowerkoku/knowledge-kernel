# Hermes Tools for Agent-CMDB

Tool wrappers exposing Agent-CMDB functionality to Hermes Agent.

## Available Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cmdb_exists(entity_id)` | Check existence | Before ANY factual claim |
| `cmdb_get(entity_id)` | Get full entity + evidence | Deep reasoning about entity |
| `cmdb_assert(entity_id, kind, status)` | Binary validation | Decision requires specific state |
| `cmdb_impact(entity_id)` | Dependency analysis | BEFORE modifying infrastructure |
| `cmdb_context(agent_id)` | Pre-packaged context | Agent startup (call once) |

## Import Pattern

```python
from tools.cmdb_exists import cmdb_exists
from tools.cmdb_get import cmdb_get
from tools.cmdb_assert import cmdb_assert
from tools.cmdb_impact import cmdb_impact
from tools.cmdb_context import cmdb_context
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
```

## Testing

Each tool has corresponding test. Run:

```bash
pytest tests/test_cmdb_exists.py
pytest tests/test_cmdb_get.py
pytest tests/test_cmdb_assert.py
pytest tests/test_cmdb_impact.py
pytest tests/test_cmdb_context.py
```