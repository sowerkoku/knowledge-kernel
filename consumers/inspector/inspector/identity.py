"""Inspector — finding identity.

Defines the canonical identifiers used to track a Finding across runs:

    finding_key  = (rule_id, entity_id)
                   — logical identity. Same key means "same problem
                     still present", regardless of status or evidence.

    finding_id   = (rule_id, entity_id, status, evidence_hash)
                   — observation identity. Same id means "exactly
                     the same observation at this position".

The hash format is **stable from Inspector v0.1.0**. Changes to the
algorithm require a promotion with a version bump. This guarantee is
enforced implicitly by the test suite
(`tests/test_finding_id.py:test_identifier_*` and
`tests/test_runs_diff.py:test_finding_id_format`).

This module exposes the conceptual API as public names:

    finding_key        (rule_id, entity_id)             — public
    finding_identity   (rule_id, entity_id, status,
                         evidence_hash)                  — public

and one implementation detail kept private:

    _stable_finding_hash  (parts) -> 16-char hex digest   — internal

The conceptual names are what callers use. The hash function is the
mechanism behind them; callers do not need it because the conceptual
API carries no information about how the digest is computed.

    Rule of thumb:
        "Una representación puede cambiar;
         la identidad no."
"""

from __future__ import annotations

import hashlib
from typing import Optional


def _stable_finding_hash(parts: list[str]) -> str:
    """Compute the short, stable SHA-256-based hash for a finding.

    Args:
        parts: Ordered tuple of components that define the identity
               (typically [rule_id, entity_id, status, evidence_hash]).

    Returns:
        16-character hexadecimal digest.

    The hash is byte-stable for the same input list. The truncation
    to 16 hex chars (64 bits) is sufficient for in-dataset uniqueness
    and keeps IDs readable when eyeballed.

    This is an implementation detail of the conceptual identity API
    exposed above. It is private — callers should use
    finding_key() or finding_identity().
    """
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def finding_key(rule_id: str, entity_id: str) -> str:
    """Logical identity: 'same problem still present?'

    Survives changes of status or evidence_hash.
    """
    return f"{rule_id}|{entity_id}"


def finding_identity(
    *,
    rule_id: str,
    entity_id: str,
    status: str,
    evidence_hash: Optional[str] = None,
) -> str:
    """Observation identity: 'exactly the same observation?'

    Format:
        f"{rule_id}|{entity_id}|{digest[:16]}"
        where digest = sha256("{rule_id}|{entity_id}|{status}|{evidence_hash or ''}")

    Args:
        rule_id:        The rule that produced the finding.
        entity_id:      The entity the rule evaluated.
        status:         "pass" | "fail" | "skipped".
        evidence_hash:  Optional 16-char SHA digest of the entity's
                        evidence block. When None, the status component
                        alone defines the hash.

    Returns:
        Stable identifier of length 16 + len(rule_id) + len(entity_id) + 1.
    """
    payload: list[str] = [rule_id, entity_id, status]
    if evidence_hash is not None:
        payload.append(evidence_hash)
    digest = _stable_finding_hash(payload)
    return f"{rule_id}|{entity_id}|{digest}"


# Re-export for backward compatibility with existing imports
# (`from inspector.report import finding_identifier`).
def finding_identifier(finding: "Finding") -> str:  # type: ignore[name-defined]
    """Backward-compatible wrapper for report.py callers.

    Given a Finding object, extracts the identity inputs and returns
    the observation identifier. Equivalent to:
        finding_identity(
            rule_id=f.rule_id,
            entity_id=f.entity_id,
            status=f.status,
            evidence_hash=f.evidence.entity_hash if (f.evidence and f.evidence.entity_hash is not None) else None,
        )
    """
    evidence_hash = None
    if finding.evidence is not None and finding.evidence.entity_hash is not None:
        evidence_hash = finding.evidence.entity_hash
    return finding_identity(
        rule_id=finding.rule_id,
        entity_id=finding.entity_id,
        status=finding.status,
        evidence_hash=evidence_hash,
    )
