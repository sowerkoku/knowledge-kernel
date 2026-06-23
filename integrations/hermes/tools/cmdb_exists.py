"""
Hermes Tool: cmdb_exists

Check if an entity exists in Agent-CMDB before making factual claims.

Usage in Hermes:
    From user message: "Does Ollama exist?"
    Tool call: cmdb_exists(entity_id="ollama")
    Response: "Yes, Ollama exists in CMDB (kind: software)"
              "No, Redis not found in CMDB"
"""

from cmdb import cmdb_exists as _cmdb_exists
from pathlib import Path


ENTITIES_DIR = Path("/home/carlos/registry")


def cmdb_exists(entity_id: str) -> dict:
    """
    Check if an entity exists in Agent-CMDB.
    
    **Use this BEFORE making ANY factual claim about infrastructure.**
    
    Args:
        entity_id: Entity identifier (e.g., "ollama", "server-53", "mysql")
    
    Returns:
        dict with keys:
        - exists: bool
        - kind: str (if exists)
        - status: str (if exists)
        - confidence: str
        - similar_entities: list (if not found)
    
    Example:
        ```python
        result = cmdb_exists("ollama")
        
        if result["exists"]:
            print(f"✓ {result['entity_id']} exists ({result['kind']})")
        else:
            print(f"✗ {result['entity_id']} not found")
            if result.get("similar_entities"):
                print(f"  Similar: {', '.join(result['similar_entities'])}")
        ```
    
    Behavioral rule:
    - ALWAYS call this before stating "X exists" or "X does not exist"
    - NEVER assume existence from memory
    """
    result = _cmdb_exists(entity_id, ENTITIES_DIR)
    return result