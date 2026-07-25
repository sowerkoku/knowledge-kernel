"""Inspector rule: no_declared_relations.

Asserts whether an entity declares any relations at all. The rule
measures the *fact*. Whether that fact signifies an issue is a
policy / operator decision.

Scope:
    `ignored_kinds` and `ignored_statuses` are policy. The default
    is to inspect ALL kinds and statuses. Operators may filter out
    classes that are commonly relation-less by convention (e.g.
    leaf UI endpoints, archived credentials).
    `required_relation_types` (default empty) — when non-empty, the
    rule only counts relations whose `type` is in the tuple. Empty
    means "any relation counts".

Falsability:
    A FAIL finding becomes PASS iff
        exists r in entity.relations where
            (required_relation_types empty or r.type in required_relation_types)
            # for the *kept* kinds after ignored_kinds/ignored_statuses filter
    The falsation is expressed as the observable condition, not as
    a required repair.

Severity:
    The rule returns status='fail' severity='warning' for factually
    zero relations; severity is *not* an architectural verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Tuple

from inspector.evidence import collect_evidence
from inspector import __version__ as INSPECTOR_VERSION
from inspector.rule import Finding, Rule


DEFAULT_IGNORED_KINDS: Tuple[str, ...] = ()
DEFAULT_IGNORED_STATUSES: Tuple[str, ...] = ()
DEFAULT_REQUIRED_RELATION_TYPES: Tuple[str, ...] = ()


@dataclass(frozen=True)
class NoDeclaredRelationsRule:
    """no_declared_relations rule — conforms to inspector.rule.Rule protocol."""

    id: str = "no_declared_relations"
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
        ignored_kinds = tuple(policy.get("ignored_kinds", DEFAULT_IGNORED_KINDS))
        ignored_statuses = tuple(
            policy.get("ignored_statuses", DEFAULT_IGNORED_STATUSES),
        )
        required_types = tuple(
            policy.get("required_relation_types", DEFAULT_REQUIRED_RELATION_TYPES),
        )

        # Step 1: materialise candidate entity ids. When caller passes
        # None we use the full list (cheap, no per-id fetch just for
        # kind/status). When caller passes explicit IDs we honour them —
        # the policy filter is reapplied later against fetched status/kind,
        # so policy cannot be bypassed by passing IDs directly.
        if entity_ids is None:
            entity_ids = sorted(m["id"] for m in api.cmdb_list())

        for eid in entity_ids:
            evidence = collect_evidence(
                api=api, entity_id=eid, inspector_version=INSPECTOR_VERSION,
            )
            yield self._judge(
                evidence, api, eid, required_types,
                ignored_kinds, ignored_statuses, now,
            )

    def _judge(
        self,
        evidence,
        api,
        entity_id: str,
        required_types: Tuple[str, ...],
        ignored_kinds: Tuple[str, ...],
        ignored_statuses: Tuple[str, ...],
        now: datetime,
    ) -> Finding:
        # Skipped when there's no evidence at all.
        if evidence.observed_at is None:
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="skipped",
                severity="info",
                message="No evidence present — cannot evaluate relations.",
                evidence=evidence,
                policy={
                    "rule_id": self.id,
                    "ignored_kinds": list(ignored_kinds),
                    "ignored_statuses": list(ignored_statuses),
                    "required_relation_types": list(required_types),
                    "reference_now": now.isoformat(),
                },
                falsation={"evidence_must_be_present": True},
            )

        result = api.cmdb_get(entity_id)
        if not result.exists or result.entity is None:
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="skipped",
                severity="info",
                message="Entity does not exist — cannot evaluate relations.",
                evidence=evidence,
                policy={
                    "rule_id": self.id,
                    "ignored_kinds": list(ignored_kinds),
                    "ignored_statuses": list(ignored_statuses),
                    "required_relation_types": list(required_types),
                    "reference_now": now.isoformat(),
                },
                falsation={"entity_must_exist": True},
            )

        entity = result.entity
        raw_kind = entity.kind
        raw_status = entity.status

        # If this entity slips past the pre-filter (filtering was applied
        # at list time only when entity_ids is None), still gate here for
        # explicitness. This bypass path is rare but keeps the rule
        # correct when callers pass entity_ids directly.
        if raw_kind in ignored_kinds or raw_status in ignored_statuses:
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="skipped",
                severity="info",
                message=f"Entity filtered: kind={raw_kind}, status={raw_status}.",
                evidence=evidence,
                policy={
                    "rule_id": self.id,
                    "ignored_kinds": list(ignored_kinds),
                    "ignored_statuses": list(ignored_statuses),
                    "required_relation_types": list(required_types),
                    "reference_now": now.isoformat(),
                },
                falsation={
                    "entity_kind_or_status_kept_only_in_dict": {
                        "kind": raw_kind,
                        "status": raw_status,
                    },
                },
            )

        relations = list(entity.relations or [])
        if required_types:
            considered = [r for r in relations if r.get("type") in required_types]
        else:
            considered = relations
        present_count = len(considered)

        if present_count > 0:
            return Finding(
                rule_id=self.id,
                entity_id=entity_id,
                status="pass",
                severity="info",
                message=f"Entity declares {present_count} relation(s); "
                        f"not excluded from analysis.",
                evidence=evidence,
                policy={
                    "rule_id": self.id,
                    "ignored_kinds": list(ignored_kinds),
                    "ignored_statuses": list(ignored_statuses),
                    "required_relation_types": list(required_types),
                    "reference_now": now.isoformat(),
                },
                falsation={
                    "pass_condition":
                        "considered relations count > 0",
                    "considered_count": present_count,
                    # Filtered-out relations kept distinct from considered.
                    "raw_relations_count": len(relations),
                },
            )

        return Finding(
            rule_id=self.id,
            entity_id=entity_id,
            status="fail",
            severity="warning",
            message=f"Entity declares 0 considered relations "
                    f"(raw relations: {len(relations)}).",
            evidence=evidence,
            policy={
                "rule_id": self.id,
                "ignored_kinds": list(ignored_kinds),
                "ignored_statuses": list(ignored_statuses),
                "required_relation_types": list(required_types),
                "reference_now": now.isoformat(),
            },
            falsation={
                "considered_count_must_be_gt": 0,
                "considered_count_actual": 0,
                "raw_relations_count": len(relations),
                # The operator-visible facts:
                "raw_kind": raw_kind,
                "raw_status": raw_status,
                "filter_used": {
                    "ignored_kinds": list(ignored_kinds),
                    "ignored_statuses": list(ignored_statuses),
                    "required_relation_types": list(required_types),
                },
            },
        )


RULE = NoDeclaredRelationsRule()
