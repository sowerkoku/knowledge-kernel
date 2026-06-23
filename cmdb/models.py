"""
Agent-CMDB Data Models — Structured Results for Agent Grounding

Separates:
- Entity: declared reality (id, kind, status, relations)
- Evidence: why we trust this data (source, validation, hash)
- QueryContext: when/how the query ran
- CMDBResult: composed result for agent consumption
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ConfidenceLevel(Enum):
    """
    Closed enum for data quality levels.
    
    verified: YAML validated against schema v1
    declared: YAML exists but not validated
    discovered: auto-discovered (e.g., from docker scan)
    inferred: deduced from relations (not direct fact)
    unknown: minimal or no validation
    """
    VERIFIED = "verified"
    DECLARED = "declared"
    DISCOVERED = "discovered"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """
    Declared reality — what exists, without trust metadata.
    
    Never includes:
    - when it was queried
    - who queried it
    - validation status
    - source file
    """
    id: str
    kind: str
    status: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    relations: List[dict] = field(default_factory=list)


@dataclass
class Evidence:
    """
    Why we trust this entity.
    
    Answers: "Where did this fact come from?"
    """
    source_file: str
    source_type: str = "cmdb_yaml"
    schema_version: Optional[int] = None
    validated: bool = False
    entity_hash: Optional[str] = None  # SHA256[:16]
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    confidence_reasons: List[str] = field(default_factory=list)


@dataclass
class QueryContext:
    """
    Query execution metadata.
    
    NOT part of the entity — belongs to the query.
    """
    queried_at: str = field(default_factory=lambda: datetime.now().isoformat())
    cmdb_version: str = "1.0.0"
    entities_dir: Optional[str] = None


@dataclass
class CMDBResult:
    """
    Composed result for agent consumption.
    
    Separates:
    - entity: what exists
    - evidence: why we trust it
    - context: when queried
    
    Usage:
        result = cmdb_get("ollama")
        
        # Facts
        print(result.entity.id, result.entity.kind)
        
        # Trust
        print(result.evidence.confidence_level)
        print(result.evidence.confidence_reasons)
        
        # Citation
        print(f"Source: {result.evidence.source_file}")
        print(f"Queried at: {result.context.queried_at}")
    """
    exists: bool
    entity: Optional[Entity] = None
    evidence: Optional[Evidence] = None
    context: Optional[QueryContext] = None
    
    # For non-existent entities
    entity_id: Optional[str] = None
    reason: Optional[str] = None
    similar_entities: List[str] = field(default_factory=list)
    
    # Backward compatibility (for transition)
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        result = {
            "exists": self.exists,
        }
        
        if self.entity:
            result["entity"] = {
                "id": self.entity.id,
                "kind": self.entity.kind,
                "status": self.entity.status,
                "metadata": self.entity.metadata,
            }
        
        if self.evidence:
            result["confidence"] = {
                "level": self.evidence.confidence_level.value,
                "reason": self.evidence.confidence_reasons,
            }
            result["provenance"] = {
                "source_file": self.evidence.source_file,
                "source_type": self.evidence.source_type,
                "schema_version": self.evidence.schema_version,
                "validated": self.evidence.validated,
                "entity_hash": self.evidence.entity_hash,
            }
        
        if self.context:
            result["query_context"] = {
                "queried_at": self.context.queried_at,
                "cmdb_version": self.context.cmdb_version,
            }
        
        if not self.exists:
            result["entity_id"] = self.entity_id
            result["reason"] = self.reason
            result["similar_entities"] = self.similar_entities
        
        return result