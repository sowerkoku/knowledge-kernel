"""
Hermes Tool: cmdb_get

Get full entity details with evidence from Agent-CMDB.

Returns:
- entity: id, kind, status, metadata
- evidence: source, validation, confidence, hash
- context: queried_at timestamp
"""

from cmdb import cmdb_get as _cmdb_get
from pathlib import Path


ENTITIES_DIR = Path("/home/carlos/registry")


def cmdb_get(entity_id: str) -> dict:
    """
    Get complete entity information with evidence.
    
    **Use this when you need to understand an entity deeply.**
    
    Returns most complete factual grounding available:
    - What it is (kind, status)
    - Where defined (source file)
    - How trustworthy (confidence level, reasons)
    - When verified (query timestamp)
    - Change detection (entity hash)
    
    Args:
        entity_id: Entity identifier
    
    Returns:
        dict with keys:
        - exists: bool
        - entity: {id, kind, status, metadata}
        - evidence: {source_file, source_type, schema_version, validated, entity_hash, confidence_level, confidence_reasons}
        - context: {queried_at, cmdb_version}
    
    Example:
        ```python
        result = cmdb_get("ollama")
        
        if result["exists"]:
            entity = result["entity"]
            evidence = result["evidence"]
            
            print(f"Entity: {entity['id']} ({entity['kind']})")
            print(f"Status: {entity['status']}")
            print(f"Source: {evidence['source_file']}")
            print(f"Validated: {evidence['validated']}")
            print(f"Confidence: {evidence['confidence_level']} ({', '.join(evidence['confidence_reasons'])})")
            print(f"Hash: {evidence['entity_hash']}")  # For change detection
        ```
    
    Behavioral rules:
    - Check confidence_level before making strong claims
    - Cite source_file when stating facts
    - Use entity_hash for change detection across queries
    - Check context.queried_at for temporal reasoning
    """
    result = _cmdb_get(entity_id, ENTITIES_DIR)
    return result.to_dict()