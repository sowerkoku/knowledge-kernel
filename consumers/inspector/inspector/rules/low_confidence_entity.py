"""Inspector rule: low_confidence_entity.

Asserts whether an entity's evidence carries a confidence level at or
above an operator-configurable minimum.

The minimum threshold is policy. The rule reports FAIL when the
observed confidence is below the minimum, PASS when it is at or above
it. Skipped when the entity has no evidence.

Scope: entity-level confidence only. The Knowledge Kernel public API
does not expose confidence per relation; this rule does not attempt
to synthesise that. See `inspector/NOTES.md` for the parked
`low_confidence_dependency` candidate.

Falsability:
    A FAIL finding becomes PASS iff `evidence.confidence_level` rises
    to the policy minimum or higher (the same entity, re-validated).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from inspector.evidence import collect_evidence
from inspector import __version__ as INSPECTOR_VERSION
from inspector.rule import Finding, Rule


DEFAULT_MINIMUM_CONFIDENCE = "MEDIUM"


# Confidence levels in INCREASING order. The rule accepts the
# name of the minimum acceptable level and compares strictly with
# this order. Levels not in this list are reported as fail (skipped
# only when evidence is absent).
LEVEL_ORDER = ("UNKNOWN", "LOW", "MEDIUM", "HIGH")


@dataclass(frozen=True)
class LowConfidenceEntityRule:
    """low_confidence_entity rule — conforms to inspector.rule.Rule protocol."""

    id: str = "low_confidence_entity"
    version: str = "0.1.0"
    consumes_api: tuple = ("cmdb_list", "cmdb_get", "cmdb_engine_info")
    consumes_entities: tuple = ("all",)

    def evaluate(
        self,
        api,
        policy: dict,
        now: datetime,
        entity_ids: Optional[Iterable[str]] = None,
    ) -> Iterable[Finding]:
        if entity_ids is None:
            entity_ids = [e["id"] for e in api.cmdb_list()]

        minimum = str(policy.get("minimum_confidence", DEFAULT_MINIMUM_CONFIDENCE))
        if minimum not in LEVEL_ORDER:
            raise ValueError(
                f"Policy minimum_confidence must be one of {LEVEL_ORDER}, "
                f"got {minimum!r}"
            )
        minimum_rank = LEVEL_ORDER.index(minimum)

        for eid in sorted(entity_ids):
            evidence = collect_evidence(
                api=api, entity_id=eid, inspector_version=INSPECTOR_VERSION,
            )
            yield self._judge(evidence, minimum, minimum_rank, now)

    def _judge(
        self,
        evidence,
        minimum: str,
        minimum_rank: int,
        now: datetime,
    ) -> Finding:
        observed_level = evidence.confidence_level
        # Surface a skipped finding for entities that exist but carry
        # no evidence (not a confidence violation — methodology gap).
        if evidence.observed_at is None or observed_level is None:
            return Finding(
                rule_id=self.id,
                entity_id=evidence.entity_id,
                status="skipped",
                severity="info",
                message="No evidence present — cannot evaluate confidence.",
                evidence=evidence,
                policy={"rule_id": self.id,
                        "minimum_confidence": minimum,
                        "reference_now": now.isoformat()},
                falsation={"evidence_must_be_present": True},
            )

        observed_rank = LEVEL_ORDER.index(observed_level) \
            if observed_level in LEVEL_ORDER else -1
        is_below = observed_rank < minimum_rank

        if is_below:
            return Finding(
                rule_id=self.id,
                entity_id=evidence.entity_id,
                status="fail",
                severity="warning",
                message=f"Confidence={observed_level!s} is below policy "
                        f"minimum={minimum}.",
                evidence=evidence,
                policy={"rule_id": self.id,
                        "minimum_confidence": minimum,
                        "reference_now": now.isoformat()},
                falsation={
                    "confidence_level_must_be_in": (
                        LEVEL_ORDER[minimum_rank:],
                    ),
                    "current_confidence_level": observed_level,
                    "minimum_required_for_pass": minimum,
                },
            )

        return Finding(
            rule_id=self.id,
            entity_id=evidence.entity_id,
            status="pass",
            severity="info",
            message=f"Confidence={observed_level!s} meets policy "
                    f"minimum={minimum}.",
            evidence=evidence,
            policy={"rule_id": self.id,
                    "minimum_confidence": minimum,
                    "reference_now": now.isoformat()},
            falsation={
                "pass_condition":
                    f"confidence_level >= {minimum}",
                "current_confidence_level": observed_level,
            },
        )


# Module-level singleton.
RULE = LowConfidenceEntityRule()
