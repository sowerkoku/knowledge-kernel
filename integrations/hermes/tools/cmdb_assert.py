"""
Hermes Tool: cmdb_assert

Binary validation: Does entity exist with expected properties?

Returns simple valid=True/False for agent decision-making.
Agents reason better with binary checks than complex structures.
"""

from cmdb import cmdb_assert as _cmdb_assert
from pathlib import Path


ENTITIES_DIR = Path("/home/carlos/registry")


def cmdb_assert(entity_id: str, expected_kind: str = None, expected_status: str = None) -> dict:
    """
    Assert that entity exists with expected properties.
    
    **Use this when decision requires specific entity state.**
    
    Binary result simplifies agent reasoning:
    - valid=True → Safe to proceed
    - valid=False → Adjust plan
    
    Args:
        entity_id: Entity to check
        expected_kind: Expected kind (optional, e.g., "software", "asset")
        expected_status: Expected status (optional, e.g., "operational")
    
    Returns:
        dict with keys:
        - valid: bool (TRUE if all assertions pass)
        - fact: str (what was asserted)
        - confidence: str
        - reason: str (if invalid, explains why failed)
        - actual_kind: str (if kind mismatch)
        - actual_status: str (if status mismatch)
    
    Example:
        ```python
        # Before installing software
        result = cmdb_assert("mysql", expected_kind="software")
        
        if result["valid"]:
            print("✓ Safe to proceed with MySQL installation")
        else:
            print(f"✗ {result['reason']}")
            # Adjust plan
        ```
    
    Behavioral rules:
    - Use before ANY infrastructure modification
    - If valid=False, NEVER proceed without explanation
    - Report reason explicitly to user
    """
    result = _cmdb_assert(entity_id, expected_kind, expected_status, ENTITIES_DIR)
    return result