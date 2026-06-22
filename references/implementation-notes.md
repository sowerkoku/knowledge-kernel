# Registry Skill — Implementation Notes

## API Contract v1.0

### Functions and their outputs

```python
registry_get(id: str)
  → dict | None
  → Full entity if found, None otherwise

registry_list(category: str | None = None)
  → list[dict]  # summaries: {id, category, type, name, status, tags}

registry_search(query: str)
  → list[dict]  # {id, name, category, match_field, score}

registry_dependencies(id: str, recursive: bool = False)
  → {
      "functional": [...],      # BFS over depends_on
      "infrastructure": [...]   # runs_on 1-hop direct (NOT BFS)
    }

registry_dependents(id: str, recursive: bool = False)
  → {
      "functional": [...],      # inverse BFS over depends_on
      "infrastructure": [...]   # directional lookup:
                                 #   if asset: entities running on it
                                 #   if non-asset: co-located entities
    }

registry_validate()
  → {
      "valid": bool,
      "errors": [{"file": str, "error": str}],
      "warnings": [{"file": str, "warning": str}],
      "stats": {"total": int, "by_category": dict}
    }
```

### Dual-graph resolver concept

The system is a **dual-graph resolver + indexed entity store**:

```
┌─────────────────────────────────────────────────────────────┐
│  DEPENDENCY GRAPH                                           │
│  Edge: depends_on                                           │
│  Type: directed graph (BFS)                                 │
│  Traversable: YES                                           │
│  part_of: NOT traversed                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE INDEX                                        │
│  Edge: runs_on                                               │
│  Type: attribute-based lookup (1-hop only)                 │
│  Traversable: NO (no transitive closure)                    │
│  Operation: co-location query / group by host               │
└─────────────────────────────────────────────────────────────┘
```

### Critical rule: runs_on is NOT a graph

When Carlos reviewed the design, he caught a critical error:

```
❌ WRONG: runs_on as graph (transitive BFS)
✅ RIGHT: runs_on as attribute (1-hop lookup only)
```

Why this matters:

```
mysql runs_on orange-pi-54
ollama runs_on orange-pi-54
hermes depends_on ollama

If runs_on were a graph:
  hermes → ollama → orange-pi-54 → mysql  ← FALSE RELATION

With attribute lookup:
  hermes.depends_on = [ollama] ✓
  hermes.runs_on = [orange-pi-54] ✓
  No cross-contamination between the two domains
```

### Infrastructure resolution is type-dependent

```python
def infrastructure_lookup(id, category):
    if category == "assets":
        # "What runs on this asset?" → reverse runs_on
        return get_entities_running_on(id)
    else:
        # "What runs on the same host as me?" → forward + reverse
        hosts = get_runs_on(id)
        result = []
        for host in hosts:
            result.extend(get_entities_running_on(host))
        return sorted(set(result))
```

### Testing the semantic separation

```python
# hermes depends on ollama
# ollama runs on orange-pi-54
# mysql runs on orange-pi-54

registry_dependencies("hermes", recursive=True)
→ functional: ["ollama"]        # BFS over depends_on
→ infrastructure: ["orange-pi-54"]  # 1-hop, NOT ["ollama", "orange-pi-54"]

registry_dependents("orange-pi-54")
→ functional: []                    # nothing depends_on orange-pi-54
→ infrastructure: [mysql, ollama, hermes, ...]  # all running on it

# NOT the same as registry_dependents("mysql") which returns
# functional: [sync-firebird-mysql, backup-mysql-job, metabase]
```

### Index structure (6 indices)

```python
_by_id              # {id: entity_dict}
_by_category       # {category: [id, ...]}
_depends_on_index  # {id: set(depends_on ids)}
_rdepends_index    # {id: set(dependents ids)}  # inverse of depends_on
_runs_on_index     # {id: set(runs_on ids)}
_rruns_on_index    # {id: set(entities running on this)}  # inverse
```

### Validation rules

The skill validates:
1. YAML parseable
2. Required fields: id, category, type, name, description
3. IDs globally unique
4. Valid categories
5. Relations point to existing IDs

The skill does NOT validate:
- That runs_on points only to assets (editor responsibility)
- Internal schema of categories
- Consistency of optional fields

This is by design: the skill is a read-only resolver, not a schema enforcer.