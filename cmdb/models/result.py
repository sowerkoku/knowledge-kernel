"""
Agent-CMDB Result Model — Composed Response for Agents

Combines Entity + Evidence + Context into single result object.

This is the primary interface for agent consumption.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from .entity import Entity
from .evidence import Evidence
from .context import QueryContext


@dataclass
class CMDBResult:
    """
    Composed result for agent consumption.
    
    Separates:
    - entity: WHAT exists (declared reality)
    - evidence: WHY we trust it (trust metadata)
    - context: WHEN queried (execution metadata)
    
    Design principle:
    Agents should NEVER receive unverified facts without evidence.
    
    Usage:
        result = cmdb_get("ollama")
        
        # Access facts
        if result.exists:
            print(f"{result.entity.id} is {result.entity.kind}")
        
        # Check evidence quality
        if result.evidence.confidence_level == ConfidenceLevel.VERIFIED:
            # Safe to make strong claims
        else:
            # Express uncertainty
        
        # Cite source
        print(f"Source: {result.evidence.source_file}")
        
        # Check staleness
        from datetime import datetime
        queried = datetime.fromisoformat(result.context.queried_at)
        age = datetime.now() - queried
        if age.total_seconds() > 3600:
            # Data might be stale
    
    For non-existent entities:
        result = cmdb_get("redis")  # Redis not in CMDB
        
        if not result.exists:
            print(f"Not found: {result.entity_id}")
            print(f"Similar: {result.similar_entities}")
    """
    
    # Core
    exists: bool
    entity: Optional[Entity] = None
    evidence: Optional[Evidence] = None
    context: Optional[QueryContext] = None
    
    # For non-existent entities
    entity_id: Optional[str] = None
    reason: Optional[str] = None
    similar_entities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary for JSON/backward compatibility.
        
        Structure:
        {
            "exists": true,
            "entity": { ... },
            "evidence": { ... },
            "context": { ... }
        }
        """
        result = {"exists": self.exists}
        
        if self.entity:
            result["entity"] = self.entity.to_dict()
        
        if self.evidence:
            result["evidence"] = self.evidence.to_dict()
        
        if self.context:
            result["context"] = self.context.to_dict()
        
        if not self.exists:
            result["entity_id"] = self.entity_id
            result["reason"] = self.reason
            result["similar_entities"] = self.similar_entities
        
        return result
    
    # Backward compatibility alias
    def to_dict_legacy(self) -> Dict[str, Any]:
        """
        Legacy dict format for transition period.
        
        Matches previous flat structure:
        {
            "exists": true,
            "entity": {...},
            "confidence": {...},
            "provenance": {...},
            "query_context": {...}
        }
        """
        if not self.exists:
            return {
                "exists": False,
                "entity_id": self.entity_id,
                "reason": self.reason,
                "similar_entities": self.similar_entities,
            }
        
        d = {
            "exists": True,
            "entity": self.entity.to_dict() if self.entity else None,
        }
        
        if self.evidence:
            e = self.evidence
            d["confidence"] = {
                "level": e.confidence_level.value,
                "reason": e.confidence_reasons,
            }
            d["provenance"] = {
                "source_file": e.source_file,
                "source_type": e.source_type_label,
                "schema_version": e.schema_version,
                "validated": e.validated,
                "entity_hash": e.entity_hash,
            }
        
        if self.context:
            d["query_context"] = self.context.to_dict()
        
        return d