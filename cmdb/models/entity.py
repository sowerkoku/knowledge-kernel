"""
Agent-CMDB Entity Model — Declared Reality

Represents WHAT exists, WITHOUT trust metadata.

NEVER includes:
- source file
- validation status
- query timestamp
- confidence level

Those belong to Evidence and QueryContext.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Entity:
    """
    Declared reality — what exists.
    
    Usage by agents:
    - Access factual attributes (id, kind, status)
    - Use in reasoning: "If entity.kind == 'software' and entity.status == 'operational'..."
    - Never cite as opinion: entity.metadata does not contain recommendations
    
    Schema:
        id: str — unique identifier (kebab-case, e.g., "ollama", "server-53")
        kind: str — entity type (asset | software | automation | data | endpoint)
        status: str — operational state (operational | degraded | down | deprecated)
        metadata: dict — additional context (name, description, version, etc.)
    """
    id: str
    kind: str
    status: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Entity":
        """Create Entity from dictionary (backward compatibility)."""
        return cls(
            id=data.get("id", ""),
            kind=data.get("kind", "unknown"),
            status=data.get("status"),
            metadata=data.get("metadata", {}),
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "kind": self.kind,
            "status": self.status,
            "metadata": self.metadata,
        }