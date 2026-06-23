"""
CMDB Assertions — Binary Checks for Agent Reasoning

Provides validation functions that return clear true/false for agent decision-making.

Agents reason better with binary validations than complex structures.
"""

from pathlib import Path
from typing import Optional, List

from .query import cmdb_get, cmdb_exists, cmdb_search
from .impact import cmdb_impact
from .models import ConfidenceLevel, SourceType


def cmdb_assert(
    entity_id: str,
    expected_kind: Optional[str] = None,
    expected_status: Optional[str] = None,
    entities_dir: Optional[Path] = None,
) -> dict:
    """
    Assert that an entity exists with expected properties.
    
    Returns binary result for agent reasoning.
    
    Usage:
        result = cmdb_assert("ollama", expected_kind="software")
        
        if result["valid"]:
            # Safe to proceed
        else:
            # Assertion failed — adjust plan
    
    Args:
        entity_id: Entity to check
        expected_kind: Expected kind (optional)
        expected_status: Expected status (optional)
        entities_dir: Path to entities
    
    Returns:
        {
            "valid": bool,
            "fact": str,
            "confidence": str,
            "reason": str (if invalid),
            "evidence": {...} (if valid)
        }
    """
    result = cmdb_get(entity_id, entities_dir)
    
    if not result.exists:
        return {
            "valid": False,
            "fact": f"Entity '{entity_id}' does not exist in CMDB",
            "confidence": "verified_absence",
            "reason": "Entity not found",
            "similar_entities": result.similar_entities,
        }
    
    # Check kind
    if expected_kind and result.entity.kind != expected_kind:
        return {
            "valid": False,
            "fact": f"Expected {entity_id} to be kind='{expected_kind}'",
            "confidence": "verified",
            "reason": f"Actual kind is '{result.entity.kind}'",
            "actual_kind": result.entity.kind,
        }
    
    # Check status
    if expected_status and result.entity.status != expected_status:
        return {
            "valid": False,
            "fact": f"Expected {entity_id} to be status='{expected_status}'",
            "confidence": "verified",
            "reason": f"Actual status is '{result.entity.status}'",
            "actual_status": result.entity.status,
        }
    
    # All assertions passed
    return {
        "valid": True,
        "fact": f"{entity_id} exists" + (f" as {expected_kind}" if expected_kind else ""),
        "confidence": result.evidence.confidence_level.value,
        "evidence": result.evidence.to_dict(),
        "entity": result.entity.to_dict(),
    }


def cmdb_context(
    agent_id: str,
    entities_dir: Optional[Path] = None,
) -> dict:
    """
    Get pre-packaged context for a specific agent.
    
    Instead of making 20 queries at startup, agent gets:
    - Its own entity
    - Known dependencies
    - Known consumers
    - Risk warnings
    
    Usage:
        ctx = cmdb_context("hermes-arquitectobi")
        
        # Pre-loaded context
        print(f"I run on: {ctx['runs_on']}")
        print(f"I use: {ctx['uses']}")
        print(f"Depends on me: {ctx['dependents']}")
    
    Returns:
        {
            "identity": agent_id,
            "known_environment": {
                "runs_on": ["server-53"],
                "uses": ["ollama", "telegram"],
                "status": "operational"
            },
            "dependents": [
                {"id": "telegram-bot", "kind": "automation"}
            ],
            "warnings": [
                "ollama has no redundancy"
            ]
        }
    """
    from .validator import load_entities_with_paths
    entities_dir = entities_dir or Path("/home/carlos/registry")
    entities, paths = load_entities_with_paths(entities_dir)
    
    if agent_id not in entities:
        return {
            "identity": agent_id,
            "error": f"Agent '{agent_id}' not found in CMDB",
            "known_environment": {},
            "dependents": [],
            "warnings": [],
        }
    
    # Get raw entity dict (includes relations at top level)
    raw_entity = entities[agent_id]
    result = cmdb_get(agent_id, entities_dir)
    
    # Extract relations by type from raw entity
    runs_on = []
    uses = []
    reads = []
    writes = []
    calls = []
    
    relations = raw_entity.get("relations", [])
    
    for rel in relations:
        rel_type = rel.get("type")
        rel_target = rel.get("target")
        
        if rel_type == "runs_on":
            runs_on.append(rel_target)
        elif rel_type == "uses":
            uses.append(rel_target)
        elif rel_type == "reads":
            reads.append(rel_target)
        elif rel_type == "writes":
            writes.append(rel_target)
        elif rel_type == "calls":
            calls.append(rel_target)
    
    # Get impact (who depends on this agent)
    impact = cmdb_impact(agent_id, entities_dir)
    dependents = [d for d in impact["depends_on_me"]["direct"]] if impact["exists"] else []
    
    # Generate warnings based on dependencies
    warnings = []
    
    # Check for single points of failure in dependencies
    for dep in uses:
        dep_impact = cmdb_impact(dep, entities_dir)
        if dep_impact["exists"]:
            risk = dep_impact["risk_indicators"]
            if risk["single_point_of_failure"] and risk["total_dependents"] > 0:
                warnings.append(f"{dep} has no redundancy (SPOF)")
    
    # Check if this agent is critical for others
    if len(dependents) > 3:
        warnings.append(f"This agent is critical for {len(dependents)} dependents")
    
    return {
        "identity": agent_id,
        "known_environment": {
            "kind": result.entity.kind,
            "status": result.entity.status,
            "runs_on": runs_on,
            "uses": uses,
            "reads": reads,
            "writes": writes,
            "calls": calls,
        },
        "dependents": dependents,
        "warnings": warnings,
        "evidence": result.evidence.to_dict() if result.evidence else None,
    }