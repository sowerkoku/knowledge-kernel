# Endpoint Identity vs Observation

Distinction emerged during agent-cmdb v1.2 (2026-07-07).

---

## The Problem

Two competing models for what an endpoint is:

**Model A — Endpoint as URL**
```yaml
id: ollama-api
kind: endpoint
metadata:
  url: http://192.168.1.54:11434    # ← identity = URL
```

**Model B — Endpoint as communication identity**
```yaml
id: ollama-api                       # ← identity = stable name
kind: endpoint
metadata:
  host: 192.168.1.54                 # ← observed fact, may change
  port: 11434                        # ← observed fact, may change
  protocol: http                     # ← observed fact, may change
```

These look similar. They are functionally different.

---

## Why Model B Wins

The ID is the communication identity. It survives the migration. Observed facts may change without breaking identity.

```yaml
# Day 1
id: ollama-api
metadata:
  host: 192.168.1.54
  port: 11434
  protocol: http

# Day 90 — same endpoint, new infrastructure
id: ollama-api                        # ← same
metadata:
  host: ollama.internal               # ← changed (DNS migration)
  port: 443                            # ← changed (HTTPS standard port)
  protocol: https                      # ← changed (TLS upgrade)
```

The agent's reasoning about "the Ollama API" is unaffected by these changes. Without Model B, every migration would break entity references and impact graphs.

---

## Where Identity vs Observation Lives

| Layer | Mutable | Role |
|-------|---------|------|
| `id` (and `kind`, `domain`) | ❌ Immutable | Stable identifier |
| `metadata.host` | ✅ Mutable | Observed fact |
| `metadata.port` | ✅ Mutable | Observed fact |
| `metadata.protocol` | ✅ Mutable | Observed fact |

This is the same pattern as `freshness`: identity is permanent in the record, observation may change without invalidating it.

---

## Anti-Pattern: Unity of Endpoint Identity and Networking

If you store connection details as primary identity:

```yaml
# ❌ WRONG — every change creates a new "entity"
id: http-192.168.1.54-11434    # ID encodes network state
metadata:
  url: http://192.168.1.54:11434
```

Problems:
- Migration creates a duplicate (or requires renaming IDs)
- Impact graphs fragment when endpoints move
- References break across the dataset
- Cannot use the endpoint's name in `exposes` cleanly

---

## When Does an Endpoint Change ID?

**Never** for routine operational changes (IP migration, port remapping, TLS).

**Only** if the endpoint's communication identity fundamentally changes:
- Service is split into two distinct APIs
- Endpoint is decommissioned and replaced by a different service
- Protocol taxonomy changes such that it's no longer the same "channel"

In those cases, mark the old entity as `status: deprecated` and create a new one.

---

## How to Query with the Right Tool

```python
# "Where do I reach ollama-api?" — current connection
endpoint = cmdb_get("ollama-api")
conn = (endpoint.evidence.metadata["host"],
        endpoint.evidence.metadata["port"],
        endpoint.evidence.metadata["protocol"])

# "What software exposes this endpoint?" — identity link
impact = cmdb_impact("ollama-api")
exposed_by = [d for d in impact["depends_on_me"]["direct"]
              if d.get("relation") == "exposes"]
# → [{id: "ollama", kind: "software", relation: "exposes"}]
```

The first query answers: "What's the current connection?"
The second query answers: "What's the same identity?"

---

## Source of Truth for the Pattern

In agent-cmdb the **relation** is identity; **metadata** is observation.

```yaml
# The relation says: "ollama exposes this endpoint"
# The metadata says: "right now you reach it this way"

relations:
  - type: exposes
    target: ollama-api            # ← identity link (stable)
metadata:
  host: 192.168.1.54              # ← observation (may change)
  port: 11434
  protocol: http
```

When the observation changes, only `metadata` updates. The relation, the impact graph, the dependents — all stable.
