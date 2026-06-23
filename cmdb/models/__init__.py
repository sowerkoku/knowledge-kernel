# Agent-CMDB Models

"""
Data models for Agent-CMDB factual memory layer.

Modules:
- entity: Declared reality (what exists)
- evidence: Trust metadata (why we believe it)
- context: Query execution metadata (when/how queried)
- result: Composed result for agent consumption
"""

from .entity import Entity
from .evidence import Evidence, SourceType, ConfidenceLevel
from .context import QueryContext
from .result import CMDBResult

__all__ = [
    "Entity",
    "Evidence",
    "SourceType",
    "ConfidenceLevel",
    "QueryContext",
    "CMDBResult",
]