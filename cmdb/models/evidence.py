"""
Agent-CMDB Evidence Model — Why We Trust This Fact

Represents WHY we can trust declared reality.

Answers:
- "Where did this fact come from?"
- "What is the quality of evidence?"
- "How can I verify this independently?"
"""

from dataclasses import dataclass, field
from datetime import datetime
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
    - Check freshness: is_fresh() method
    - Express uncertainty: "Evidence level is {evidence.confidence_level.value}"
    - Detect changes: compare evidence.entity_hash between queries
    
    Fields:
    - source_type: Origin of data (declared/discovered/imported/inferred)
    - source_file: Path to source YAML (for declared sources)
    - observed_at: When the fact was observed/verified (ISO format)
    - expires_at: When confidence expires (optional, calculated from ttl)
    - ttl_seconds: Expected time-to-live for this evidence
    - schema_version: Format version (for validated sources)
    - validated: Whether source passed validation
    - entity_hash: SHA256[:16] for change detection
    - confidence_level: Evidence quality (verified/declared/discovered/inferred/unknown)
    - confidence_reasons: Why this level was assigned
    """
    source_type: SourceType = SourceType.DECLARED
    source_file: Optional[str] = None
    source_type_label: Optional[str] = None  # "cmdb_yaml", "docker_scan", etc.
    
    # Temporal — CRITICAL for agent reasoning
    observed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    ttl_seconds: Optional[int] = None
    
    schema_version: Optional[int] = None
    validated: bool = False
    entity_hash: Optional[str] = None  # SHA256[:16]
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    confidence_reasons: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate expires_at from ttl if not set."""
        if self.ttl_seconds and not self.expires_at:
            from datetime import timedelta
            observed = datetime.fromisoformat(self.observed_at)
            expires = observed + timedelta(seconds=self.ttl_seconds)
            self.expires_at = expires.isoformat()
    
    def is_fresh(self) -> bool:
        """
        Check if evidence is still fresh (not expired).
        
        Returns True if:
        - No expires_at set (indefinite validity)
        - Current time < expires_at
        
        Returns False if:
        - Current time >= expires_at
        """
        if not self.expires_at:
            return True
        
        now = datetime.now()
        expires = datetime.fromisoformat(self.expires_at)
        return now < expires
    
    def age_seconds(self) -> float:
        """Calculate age of evidence in seconds."""
        observed = datetime.fromisoformat(self.observed_at)
        return (datetime.now() - observed).total_seconds()
    
    def time_to_expiry_seconds(self) -> Optional[float]:
        """Calculate time remaining until expiry (None if no expiry)."""
        if not self.expires_at:
            return None
        
        expires = datetime.fromisoformat(self.expires_at)
        remaining = (expires - datetime.now()).total_seconds()
        return max(0, remaining)
    
    @classmethod
    def with_default_ttl(cls, source_type: SourceType, **kwargs) -> "Evidence":
        """
        Factory with default TTL based on source type.
        
        TTL defaults:
        - DECLARED: None (no expiry — intentional declaration)
        - DISCOVERED: 3600 (1 hour — auto-discovery may go stale)
        - IMPORTED: 300 (5 min — external APIs change frequently)
        - INFERRED: 60 (1 min — inferences may be invalidated)
        """
        default_ttls = {
            SourceType.DECLARED: None,
            SourceType.DISCOVERED: 3600,
            SourceType.IMPORTED: 300,
            SourceType.INFERRED: 60,
        }
        
        ttl = kwargs.pop('ttl_seconds', default_ttls.get(source_type))
        
        return cls(
            source_type=source_type,
            ttl_seconds=ttl,
            **kwargs
        )
    
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
            # No TTL for declared facts — valid until changed
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
            # Temporal fields (critical for agent reasoning)
            "observed_at": self.observed_at,
            "expires_at": self.expires_at,
            "ttl_seconds": self.ttl_seconds,
        }