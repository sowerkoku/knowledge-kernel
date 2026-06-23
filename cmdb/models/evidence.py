"""
Agent-CMDB Evidence Model — Why We Trust This Fact

Represents WHY we can trust declared reality.

Answers:
- "Where did this fact come from?"
- "What is the quality of evidence?"
- "How can I verify this independently?"
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class SourceType(Enum):
    """
    Origin of the entity data.
    
    Critical for agent reasoning because different sources have different reliability characteristics.
    
    declared: Human-maintained YAML (intentional declaration)
    discovered: Auto-discovered via scanner (Docker, Kubernetes, etc.)
    imported: Imported from external API (Cloud provider, monitoring system)
    inferred: Deduced by reasoning engine (not directly observed)
    """
    DECLARED = "declared"
    DISCOVERED = "discovered"
    IMPORTED = "imported"
    INFERRED = "inferred"


class ConfidenceLevel(Enum):
    """
    Level of evidence supporting the fact.
    
    IMPORTANT: This measures EVIDENCE QUALITY, not truth probability.
    
    "verified" does NOT mean "99.9% true".
    It means: "Evidence meets validation criteria defined by CMDB schema."
    
    Levels:
    - verified: Validated against schema v1 (highest evidence standard)
    - declared: exists in source but not validated
    - discovered: auto-discovered, unvalidated
    - inferred: deduced by engine (may be incomplete)
    - unknown: minimal or no evidence
    """
    VERIFIED = "verified"
    DECLARED = "declared"
    DISCOVERED = "discovered"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@dataclass
class Evidence:
    """
    Trust metadata for entity facts.
    
    Usage by agents:
    - Cite source: f"According to {evidence.source_file}..."
    - Express uncertainty: "Evidence level is {evidence.confidence_level.value}"
    - Detect changes: compare evidence.entity_hash between queries
    
    Fields:
    - source_type: Origin of data (declared/discovered/imported/inferred)
    - source_file: Path to source YAML (for declared sources)
    - schema_version: Format version (for validated sources)
    - validated: Whether source passed validation
    - entity_hash: SHA256[:16] for change detection
    - confidence_level: Evidence quality (verified/declared/discovered/inferred/unknown)
    - confidence_reasons: Why this level was assigned
    """
    source_type: SourceType = SourceType.DECLARED
    source_file: Optional[str] = None
    source_type_label: Optional[str] = None  # "cmdb_yaml", "docker_scan", etc.
    schema_version: Optional[int] = None
    validated: bool = False
    entity_hash: Optional[str] = None  # SHA256[:16]
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    confidence_reasons: List[str] = field(default_factory=list)
    
    @classmethod
    def verified(cls, source_file: str, entity_hash: str) -> "Evidence":
        """Factory for verified evidence (convenient constructor)."""
        return cls(
            source_type=SourceType.DECLARED,
            source_file=source_file,
            source_type_label="cmdb_yaml",
            schema_version=1,
            validated=True,
            entity_hash=entity_hash,
            confidence_level=ConfidenceLevel.VERIFIED,
            confidence_reasons=["yaml_validated_schema_v1"],
        )
    
    @classmethod
    def declared(cls, source_file: str, schema_version: Optional[int] = None) -> "Evidence":
        """Factory for declared (unvalidated) evidence."""
        reasons = []
        if schema_version:
            reasons.append(f"schema_v{schema_version}")
        else:
            reasons.append("no_schema_version")
        
        return cls(
            source_type=SourceType.DECLARED,
            source_file=source_file,
            source_type_label="cmdb_yaml",
            schema_version=schema_version,
            validated=False,
            confidence_level=ConfidenceLevel.DECLARED,
            confidence_reasons=reasons,
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "source_type": self.source_type.value,
            "source_file": self.source_file,
            "source_type_label": self.source_type_label,
            "schema_version": self.schema_version,
            "validated": self.validated,
            "entity_hash": self.entity_hash,
            "confidence_level": self.confidence_level.value,
            "confidence_reasons": self.confidence_reasons,
        }