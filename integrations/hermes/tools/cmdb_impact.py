"""
Hermes Tool: cmdb_impact

Analyze dependency graph: "What breaks if X fails/changes?"

Returns:
- depends_on_me: entities that depend on X (direct + transitive)
- i_depend_on: entities that X depends on
- affected_layers: grouped by kind (software, automation, data, etc.)
- risk_indicators: factual signals (SPOF, critical_dependents, etc.)
"""

from cmdb import cmdb_impact as _cmdb_impact
from pathlib import Path


ENTITIES_DIR = Path("/home/carlos/registry")


def cmdb_impact(entity_id: str) -> dict:
    """
    Analyze impact of entity failure/modification.
    
    **ALWAYS call this BEFORE modifying ANY infrastructure.**
    
    Answers:
    - "What depends on X?"
    - "What layers are affected?"
    - "Is X a single point of failure?"
    - "How many critical entities are at risk?"
    
    Args:
        entity_id: Entity to analyze
    
    Returns:
        dict with keys:
        - exists: bool
        - target: {id, kind, status}
        - depends_on_me: {direct: [...], transitive: [...]}
        - i_depend_on: {direct: [...], transitive: [...]}
        - affected_layers: {software: [], automation: [], data: [], ...}
        - risk_indicators: {
            total_dependents: int,
            critical_dependents: [...],
            redundancy_found: bool,
            single_point_of_failure: bool
          }
    
    Example:
        ```python
        # Before updating Ollama
        impact = cmdb_impact("ollama")
        
        print("📊 Impact Analysis for Ollama:")
        print(f"  Direct dependents: {len(impact['depends_on_me']['direct'])}")
        print(f"  Affected layers: {list(impact['affected_layers'].keys())}")
        print(f"  SPOF: {impact['risk_indicators']['single_point_of_failure']}")
        
        if impact["risk_indicators"]["single_point_of_failure"]:
            print("⚠️ WARNING: No redundancy found")
            critical = len(impact["risk_indicators"]["critical_dependents"])
            print(f"  {critical} critical dependents at risk")
            print("\nRecommend:")
            print("  1. Schedule maintenance window")
            print("  2. Notify affected users")
            print("  3. Prepare rollback plan")
        ```
    
    Behavioral rules:
    - NEVER modify infrastructure without calling this first
    - If single_point_of_failure=True, ALWAYS warn user
    - If critical_dependents > 0, recommend maintenance window
    - Present factual indicators, let user decide
    
    Separation of concerns:
    - CMDB provides: total_dependents=5, critical_dependents=[...], spof=True
    - Agent decides: "This is risky, recommend waiting"
    - User decides: "Proceed" or "Cancel"
    """
    result = _cmdb_impact(entity_id, ENTITIES_DIR)
    return result