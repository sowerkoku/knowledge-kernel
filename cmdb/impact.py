"""
CMDB Impact Analysis — Factual Dependency Graph

Answers: "What depends on X?" and "What layers are affected if X changes/fails?"

Design principles:
- Return structural facts, not recommendations
- Distinguish direct vs. transitive dependencies
- Group by affected layers (software, automation, data, endpoints)
- Include criticality signals, not business interpretations
"""

from typing import Optional
from pathlib import Path
from collections import defaultdict

from .validator import load_entities_with_paths


DEFAULT_ENTITIES_DIR = Path("/home/carlos/registry")

# Relation types that create dependencies (X depends on Y)
DEPENDENCY_RELATIONS = {"uses", "reads", "writes", "runs_on", "calls"}

# Relation types that indicate reverse dependency (Y is used by X)
REVERSE_DEPENDENCY_RELATIONS = {"owns", "monitors", "backs_up"}


def cmdb_impact(entity_id: str, entities_dir: Optional[Path] = None) -> dict:
    """
    Analyze the impact of changing or failing an entity.
    
    **Agent usage:**
    Use this before making infrastructure changes to understand blast radius.
    
    ```python
    impact = cmdb_impact("ollama")
    
    # What breaks if Ollama fails?
    if impact["exists"]:
        print(f"Direct dependents: {impact['depends_on_me']['direct']}")
        print(f"Transitive dependents: {impact['depends_on_me']['transitive']}")
        print(f"Affected layers: {impact['affected_layers']}")
    ```
    
    Args:
        entity_id: The entity to analyze (e.g., "ollama", "mysql", "server-53")
        entities_dir: Path to entities directory
    
    Returns:
        Impact analysis result.
        
        Example:
        ```python
        {
            "target": {
                "id": "ollama",
                "kind": "software",
                "status": "operational",
            },
            "exists": True,
            
            # Entities that depend ON the target (target is their dependency)
            "depends_on_me": {
                "direct": [
                    {"id": "hermes", "kind": "software", "relation": "uses"},
                ],
                "transitive": [
                    {"id": "telegram-bot", "kind": "automation", "path": ["telegram-bot", "hermes", "ollama"]},
                ],
            },
            
            # Entities that the target depends on (target is their dependent)
            "i_depend_on": {
                "direct": [
                    {"id": "server-53", "kind": "asset", "relation": "runs_on"},
                ],
                "transitive": [],
            },
            
            # Group by affected layer
            "affected_layers": {
                "software": ["hermes"],
                "automation": ["telegram-bot"],
                "data": [],
                "endpoints": [],
                "assets": [],
            },
            
            # Factual risk indicators (not recommendations)
            "risk_indicators": {
                "total_dependents": 2,
                "critical_dependents": [],  # Entities with criticality.business=high
                "redundancy_found": False,  # No alternate providers found
                "single_point_of_failure": True,  # If total_dependents > 0 and no redundancy
            },
        }
        ```
        
        If entity not found:
        ```python
        {
            "target": {"id": "redis"},
            "exists": False,
            "reason": "Entity not found in CMDB",
        }
        ```
    """
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    entities, _ = load_entities_with_paths(entities_dir)
    
    # Check if target exists
    if entity_id not in entities:
        return {
            "target": {"id": entity_id},
            "exists": False,
            "reason": "Entity not found in CMDB",
        }
    
    target = entities[entity_id]
    
    # Build dependency graph
    depends_on_me = _find_dependents(entity_id, entities)
    i_depend_on = _find_dependencies(entity_id, entities)
    
    # Group by affected layers
    affected_layers = _group_by_layer(depends_on_me)
    
    # Calculate risk indicators (factual, not interpretive)
    risk_indicators = _calculate_risk_indicators(depends_on_me, entities)
    
    return {
        "target": {
            "id": entity_id,
            "kind": target.get("kind"),
            "status": target.get("status"),
        },
        "exists": True,
        "depends_on_me": depends_on_me,
        "i_depend_on": i_depend_on,
        "affected_layers": affected_layers,
        "risk_indicators": risk_indicators,
    }


def _find_dependents(entity_id: str, entities: dict) -> dict:
    """
    Find all entities that depend on the target entity.
    
    Returns:
        {
            "direct": [{"id": "...", "kind": "...", "relation": "..."}],
            "transitive": [{"id": "...", "kind": "...", "path": [...]}],
        }
    """
    direct = []
    all_dependents = set()
    
    # Find direct dependents (entities that have a relation TO the target)
    for eid, entity in entities.items():
        if eid == entity_id:
            continue
        
        for rel in entity.get("relations", []):
            rel_type = rel.get("type")
            rel_target = rel.get("target")
            
            if rel_target == entity_id and rel_type in DEPENDENCY_RELATIONS:
                direct.append({
                    "id": eid,
                    "kind": entity.get("kind"),
                    "relation": rel_type,
                })
                all_dependents.add(eid)
    
    # Find transitive dependents (BFS)
    transitive = []
    visited = {entity_id}
    queue = [(d["id"], [d["id"], entity_id]) for d in direct]
    
    while queue:
        current_id, path = queue.pop(0)
        
        if current_id in visited:
            continue
        visited.add(current_id)
        
        # Find entities that depend on current
        for eid, entity in entities.items():
            if eid in visited:
                continue
            
            for rel in entity.get("relations", []):
                rel_target = rel.get("target")
                
                if rel_target == current_id and rel.get("type") in DEPENDENCY_RELATIONS:
                    if eid not in [d["id"] for d in direct]:  # Not already direct
                        transitive.append({
                            "id": eid,
                            "kind": entity.get("kind"),
                            "path": [eid] + path,  # Full chain
                        })
                        all_dependents.add(eid)
                        queue.append((eid, [eid] + path))
    
    return {
        "direct": direct,
        "transitive": transitive,
    }


def _find_dependencies(entity_id: str, entities: dict) -> dict:
    """
    Find all entities that the target depends on.
    
    Returns:
        {
            "direct": [{"id": "...", "kind": "...", "relation": "..."}],
            "transitive": [{"id": "...", "kind": "...", "path": [...]}],
        }
    """
    target = entities.get(entity_id)
    if not target:
        return {"direct": [], "transitive": []}
    
    direct = []
    
    # Find direct dependencies
    for rel in target.get("relations", []):
        rel_type = rel.get("type")
        rel_target = rel.get("target")
        
        if rel_type in DEPENDENCY_RELATIONS:
            direct.append({
                "id": rel_target,
                "kind": entities.get(rel_target, {}).get("kind"),
                "relation": rel_type,
            })
    
    # Find transitive dependencies (BFS)
    transitive = []
    visited = {entity_id}
    queue = [(d["id"], [entity_id, d["id"]]) for d in direct]
    
    while queue:
        current_id, path = queue.pop(0)
        
        if current_id in visited:
            continue
        visited.add(current_id)
        
        current = entities.get(current_id)
        if not current:
            continue
        
        for rel in current.get("relations", []):
            rel_target = rel.get("target")
            
            if rel_target not in visited and rel.get("type") in DEPENDENCY_RELATIONS:
                transitive.append({
                    "id": rel_target,
                    "kind": entities.get(rel_target, {}).get("kind"),
                    "path": path + [rel_target],
                })
                queue.append((rel_target, path + [rel_target]))
    
    return {
        "direct": direct,
        "transitive": transitive,
    }


def _group_by_layer(dependents: dict) -> dict:
    """
    Group dependents by architectural layer.
    """
    layers = {
        "software": [],
        "automation": [],
        "data": [],
        "endpoints": [],
        "assets": [],
    }
    
    kind_to_layer = {
        "software": "software",
        "automation": "automation",
        "data": "data",
        "endpoint": "endpoints",
        "asset": "assets",
    }
    
    # Process direct dependents
    for dep in dependents.get("direct", []):
        kind = dep.get("kind")
        layer = kind_to_layer.get(kind)
        if layer and dep["id"] not in layers[layer]:
            layers[layer].append(dep["id"])
    
    # Process transitive dependents
    for dep in dependents.get("transitive", []):
        kind = dep.get("kind")
        layer = kind_to_layer.get(kind)
        if layer and dep["id"] not in layers[layer]:
            layers[layer].append(dep["id"])
    
    return layers


def _calculate_risk_indicators(dependents: dict, entities: dict) -> dict:
    """
    Calculate factual risk indicators (not recommendations).
    """
    all_dependent_ids = set()
    critical_dependents = []
    
    # Collect all dependent IDs
    for dep in dependents.get("direct", []) + dependents.get("transitive", []):
        all_dependent_ids.add(dep["id"])
    
    # Check for critical dependents
    for dep_id in all_dependent_ids:
        dep_entity = entities.get(dep_id, {})
        criticality = dep_entity.get("criticality", {})
        
        if criticality.get("business") == "high":
            critical_dependents.append({
                "id": dep_id,
                "kind": dep_entity.get("kind"),
                "criticality": criticality,
            })
    
    # Check for redundancy (simple: are there multiple entities of same kind providing same function?)
    # This is a basic check — more sophisticated analysis would require service/function metadata
    redundancy_found = len(all_dependent_ids) > 1 and len(set(
        entities.get(d, {}).get("kind") for d in all_dependent_ids
    )) > 1
    
    total_dependents = len(all_dependent_ids)
    
    return {
        "total_dependents": total_dependents,
        "critical_dependents": critical_dependents,
        "redundancy_found": redundancy_found,
        "single_point_of_failure": total_dependents > 0 and not redundancy_found,
    }