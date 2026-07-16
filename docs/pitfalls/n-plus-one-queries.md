---
name: pitfalls/n-plus-one-queries
description: Looping over cmdb_list() with cmdb_get() per item is the N+1 pattern. Use cmdb_impact() or batch load.
applies_to:
  - performance
  - latency
  - cmdb
---

# Pitfall 5: N+1 query pattern kills latency

## Symptom

p95 latency >4000ms for simple questions like "¿Qué puertos expone app-server-01?"

## Root cause

```python
endpoints = cmdb_list(kind="endpoint")   # Returns N endpoints
for ep in endpoints:
    detail = cmdb_get(ep["id"])          # N sequential API calls
```

Each `cmdb_get()` loads + parses + validates a YAML file. N × ~120ms = seconds.

## Solution patterns

1. **Filter at list time** if the API supports relation filtering
2. **Batch load** — load once, filter in memory
3. **Cache** results for the duration of a session
4. **Direct graph traversal** — use `cmdb_impact(asset_id)` to get dependents directly

## Rule of thumb

If you're looping over `cmdb_list()` results and calling `cmdb_get()` per item,
you're doing N+1. Refactor.
