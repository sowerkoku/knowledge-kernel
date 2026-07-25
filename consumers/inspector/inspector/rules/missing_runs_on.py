"""Inspector rule: missing_runs_on.

Asserts whether an entity of a target kind has at least one
relation of type `runs_on`. Entities without this relation emit
FAIL; those with it emit PASS. Entities that don't exist emit
SKIPPED.

Scope:
    `target_kinds` is policy. The default is (`software`,) because
    that is the kind for which runs_on is semantically meaningful.
    Other kinds can be added by changing policy without contract
    changes. The rule does NOT inspect kinds the policy does not
    enumerate.

Falsability:
    A FAIL finding becomes PASS iff the entity acquires at least one
    `runs_on` relation (its existing relations, post-update, contain a
    runs_on target).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Tuple

from inspector.evidence import collect_evidence
from inspector import __version__ as INSPECTOR_VERSION
from inspector.rule import Finding, Rule


DEFAULT_TARGET_KINDS = ("software",)


@dataclass(frozen=True)
class MissingRunsOnRule:
    """missing_runs_on rule — conforms to inspector.rule.Rule protocol."""

    id: str = "missing_runs_on"
    version: str = "0.1.0"
    consumes_api: tuple = ("cmdb_list", "cmdb_get", "cmdb_engine_info")
    consumes_entities: tuple = ("by_kind", "software")

    def evaluate(
        self,
        api,
        policy: dict,
        now: datetime,
        entity_ids: Optional[Iterable[str]] = None,
    ) -> Iterable[Finding]:
        # Resolve target kinds from policy.
        target_kinds = tuple(policy.get("target_kinds", DEFAULT_TARGET_KINDS))
        if not target_kinds:
            raise ValueError("Policy target_kinds cannot be empty.")

        if entity_ids is None:
            # Filter candidates by kind. cmdb_list(kind=...) per target.
            candidates: list[str] = []
            for k in target_kinds:
                candidates.extend(
                    e["id"] for e in api.cmdb_list(kind=k)
                )
            entity_ids = sorted(set(candidates))

        for eid in entity_ids:
            evidence = collect_evidence(
                api=api, entity_id=eid, inspector_version=INSPECTOR_VERSION,
            )
            yield self._judge(evidence, api, eid, target_kinds, now)

    def _judge(
        self,
        evidence,
        api,
        entity_id: str,
        target_kinds: Tuple[str, ...],
        now: datetime,
    ) -> Finding:
        # Skipped when there's no evidence at all.
        if evidence.observed_at is None:
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="skipped",
                severity="info",
                message="No evidence — cannot evaluate runs_on.",
                evidence=evidence,
                policy={"rule_id": self.id,
                        "target_kinds": list(target_kinds),
                        "reference_now": now.isoformat()},
                falsation={"evidence_must_be_present": True},
            )

        # Pull the live relation list to evaluate absence.
        result = api.cmdb_get(entity_id)
        if not result.exists or result.entity is None:
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="skipped",
                severity="info",
                message="Entity does not exist — cannot evaluate runs_on.",
                evidence=evidence,
                policy={"rule_id": self.id,
                        "target_kinds": list(target_kinds),
                        "reference_now": now.isoformat()},
                falsation={"entity_must_exist": True},
            )

        relations = list(result.entity.relations or [])
        has_runs_on = any(r.get("type") == "runs_on" for r in relations)
        relation_summary = [
            {"type": r.get("type"), "target": r.get("target")}
            for r in relations
        ]

        if has_runs_on:
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="pass",
                severity="info",
                message=f"Entity declares {len(relations)} relation(s); "
                        f"runs_on is present.",
                evidence=evidence,
                policy={"rule_id": self.id,
                        "target_kinds": list(target_kinds),
                        "reference_now": now.isoformat()},
                falsation={
                    "pass_condition":
                        "entity.relations includes type == 'runs_on'",
                    "current_relations": relation_summary,
                },
            )

        return Finding(
            rule_id=self.id,
            entity_id=entity_id,
            status="fail",
            severity="warning",
            message=f"Entity has no runs_on relation "
                    f"({len(relations)} other relation(s) present).",
            evidence=evidence,
            policy={"rule_id": self.id,
                    "target_kinds": list(target_kinds),
                    "reference_now": now.isoformat()},
            falsation={
                "entity_must_have_relation_of_type": "runs_on",
                "current_relations": relation_summary,
            },
        )


RULE = MissingRunsOnRule()
