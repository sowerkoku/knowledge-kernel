---
name: pitfalls/asset-duplicates
description: Two assets can reference the same physical host. Keep higher schema_version, migrate references.
applies_to:
  - cleanup
  - assets
---

# Pitfall 11: Asset duplicates — same host, different IDs

## Symptom

`cmdb_list(kind="asset")` shows two entities for the same physical host.

## Example

- `app-server-01` (legacy, schema_version 1, RAM 1GB — wrong)
- `server-192-168-1-54` (new, schema_version 2, RAM 7.5Gi — accurate)

## Resolution

1. **Compare schemas** — keep the one with higher `schema_version`
2. **Compare evidence** — keep the one with more detailed metadata
3. **Find all references** before deleting:
   ```bash
   grep -r "<legacy-id>" <dataset-root>
   ```
4. **Update references** in dependent entities (assets, endpoints,
   automations that point to the legacy name)
5. **Delete the legacy asset**

## Rule: criteria for keeping an asset

- `schema_version: 2` (current standard)
- More accurate hardware data (RAM, disk, network interfaces)
- More recent `provenance.discovery_run`
- Richer evidence (observed ports, services, containers)
