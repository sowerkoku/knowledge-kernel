"""Evidence — raw facts pulled from the Knowledge Kernel.

A Evidence object is independent of any rule's verdict. The same
evidence can be consumed by multiple rules without re-querying the
Kernel.

Fields:

    api           Function name from cmdb.api used to fetch this evidence.
    entity_id     Entity the evidence describes.
    observed_at   ISO timestamp of the source observation.
    age_seconds   Computed by Kernel (evidence.age_seconds()).
    ttl_seconds   TTL declared by the entity, if any (None if not set).
    confidence_level    From evidence.confidence_level.
    confidence_basis    From evidence.confidence_basis.
    entity_hash   From evidence.entity_hash (change detection).
    dataset_hash  From cmdb_engine_info() — pin for reproducibility.
    inspector_version  Pin of the Inspector that produced the report.

This module does NOT import from cmdb.*. The api parameter is
expected to be a `KernelAPI` instance; the only module in the
Inspector that imports cmdb.* is `inspector.kernel_api`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Evidence:
    api: str
    entity_id: str
    observed_at: Optional[str]
    age_seconds: Optional[float]
    ttl_seconds: Optional[int]
    confidence_level: Optional[str]
    confidence_basis: List[str]
    entity_hash: Optional[str]
    dataset_hash: Optional[str]
    inspector_version: str = ""


# Helper kept for backward compatibility with the previous API, but the
# canonical entry point now takes a `api` and an `inspector_version`.
def collect_evidence(api, entity_id: str, inspector_version: str) -> Evidence:
    """Build Evidence for entity_id using whatever public API the
    caller passes (typically `KernelAPI` from `inspector.kernel_api`).

    Returns Evidence with empty fields when the entity does not exist;
    absence itself is the evidence. Caller decides what to do.
    """
    engine = api.cmdb_engine_info()
    result = api.cmdb_get(entity_id)
    if not result.exists or result.evidence is None or result.entity is None:
        return Evidence(
            api="cmdb_get",
            entity_id=entity_id,
            observed_at=None,
            age_seconds=None,
            ttl_seconds=None,
            confidence_level=None,
            confidence_basis=[],
            entity_hash=None,
            dataset_hash=engine.get("dataset_hash"),
            inspector_version=inspector_version,
        )
    ev = result.evidence
    basis = [str(b) for b in (ev.confidence_basis or [])]
    confidence = (
        getattr(ev.confidence_level, "name", str(ev.confidence_level))
        if ev.confidence_level else None
    )
    return Evidence(
        api="cmdb_get",
        entity_id=entity_id,
        observed_at=ev.observed_at,
        age_seconds=float(ev.age_seconds()) if ev.observed_at else None,
        ttl_seconds=ev.ttl_seconds,
        confidence_level=confidence,
        confidence_basis=basis,
        entity_hash=ev.entity_hash,
        dataset_hash=engine.get("dataset_hash"),
        inspector_version=inspector_version,
    )
