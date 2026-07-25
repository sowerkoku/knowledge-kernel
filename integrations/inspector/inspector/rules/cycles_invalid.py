"""Inspector rule: cycles_invalid (v0.1, deliberately simple).

Asserts whether the entity appears anywhere in its own transitive
dependency closure. Such self-reachability in `i_depend_on.transitive`
indicates a cycle.

Scope:
    All entities. Evaluation calls `cmdb_impact(eid).i_depend_on`.
    The value the rule reads is computed by the Kernel; the rule
    does NOT walk edges, identify minimal cycles, or build paths.

Falsability:
    A FAIL finding becomes PASS iff:
        entity_id no longer appears in
        cmdb_impact(entity_id).i_depend_on.transitive
    This is the observable condition. Any specific edge removal that
    achieves it is a *repair*, not a falsation clause.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from inspector.evidence import collect_evidence
from inspector import __version__ as INSPECTOR_VERSION
from inspector.rule import Finding, Rule


@dataclass(frozen=True)
class CyclesInvalidRule:
    """cycles_invalid rule — conforms to inspector.rule.Rule protocol."""

    id: str = "cycles_invalid"
    version: str = "0.1.0"
    consumes_api: tuple = (
        "cmdb_list", "cmdb_impact", "cmdb_get", "cmdb_engine_info",
    )
    consumes_entities: tuple = ("all",)

    def evaluate(
        self,
        api,
        policy: dict,
        now: datetime,
        entity_ids: Optional[Iterable[str]] = None,
    ) -> Iterable[Finding]:
        if entity_ids is None:
            entity_ids = sorted(e["id"] for e in api.cmdb_list())

        for eid in entity_ids:
            evidence = collect_evidence(
                api=api, entity_id=eid, inspector_version=INSPECTOR_VERSION,
            )
            yield self._judge(evidence, api, eid, now)

    def _judge(self, evidence, api, entity_id: str, now: datetime) -> Finding:
        # Skipped: entities with no observed evidence cannot be evaluated.
        if evidence.observed_at is None:
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="skipped",
                severity="info",
                message="No evidence — cannot compute dependency closure.",
                evidence=evidence,
                policy={"rule_id": self.id,
                        "reference_now": now.isoformat()},
                falsation={"evidence_must_be_present": True},
            )

        impact = api.cmdb_impact(entity_id)
        # cmdb_impact's contract: 'exists' = True iff the entity is in
        # the public dataset. The rule only operates on existing entities.
        if not impact.get("exists", False):
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="skipped",
                severity="info",
                message="Entity does not exist per cmdb_impact — cannot evaluate cycle.",
                evidence=evidence,
                policy={"rule_id": self.id,
                        "reference_now": now.isoformat()},
                falsation={"entity_must_exist": True},
            )

        i_dep = impact.get("i_depend_on", {}) or {}
        transitive = [
            d.get("id") for d in (i_dep.get("transitive") or [])
            if d.get("id")
        ]

        # A cycle exists when the entity is reachable from itself through
        # transitive dependencies. Self-reachability is the falsation.
        is_in_cycle = entity_id in transitive

        if is_in_cycle:
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="fail",
                severity="warning",
                message=f"Entity appears in its own transitive dependency "
                        f"closure ({len(transitive)} transitive dependents).",
                evidence=evidence,
                policy={"rule_id": self.id,
                        "reference_now": now.isoformat()},
                falsation={
                    "entity_not_present_in":
                        f"cmdb_impact({entity_id!r}).i_depend_on.transitive",
                    "self_reachable": False,
                    "observation": {
                        "transitive_count": len(transitive),
                        "transitive_sample": transitive[:5],
                    },
                },
            )

        return Finding(
            rule_id=self.id,
            entity_id=entity_id,
            status="pass",
            severity="info",
            message=f"Entity not self-reachable "
                    f"({len(transitive)} transitive dependents examined).",
            evidence=evidence,
            policy={"rule_id": self.id,
                    "reference_now": now.isoformat()},
            falsation={
                "pass_condition":
                    f"{entity_id!r} not in cmdb_impact.{entity_id!r}.i_depend_on.transitive",
                "self_reachable": False,
            },
        )


RULE = CyclesInvalidRule()
