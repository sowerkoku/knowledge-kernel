"""
Agent-CMDB Query Context Model — Execution Metadata

Represents WHEN and HOW a query was executed.

NEVER mixed with Entity facts.

Usage:
- Temporal reasoning: "Was this fact true 1 hour ago?"
- Caching: "Do I need to re-query or is cached data still fresh?"
- Versioning: "Which CMDB version provided this data?"
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class QueryContext:
    """
    Query execution metadata.
    
    This belongs to the QUERY, not the ENTITY.
    
    Example scenario:
    
    Query 1 (10:00 AM):
      result = cmdb_get("ollama")
      # result.context.queried_at = "2026-06-22T10:00:00"
    
    Query 2 (11:00 AM):
      result = cmdb_get("ollama")
      # result.context.queried_at = "2026-06-22T11:00:00"
    
    Entity is the same. Query context differs.
    
    Fields:
    - queried_at: When the query ran (ISO format)
    - cmdb_version: Version of CMDB that served the query
    - entities_dir: Which directory was queried (for debugging multi-CMDB setups)
    """
    queried_at: str = field(default_factory=lambda: datetime.now().isoformat())
    cmdb_version: str = "1.0.0"
    entities_dir: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "queried_at": self.queried_at,
            "cmdb_version": self.cmdb_version,
            "entities_dir": self.entities_dir,
        }