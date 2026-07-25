"""Inspector rule: stale_entity.

Asserts whether an entity's evidence is older than a configured
threshold.

Threshold and reference clock are policy. The rule reports PASS when
the evidence is fresh enough (age <= stale_after_days), FAIL when it
is too old, or FAIL with severity=warning when the evidence
timestamp sits in the future of the reference clock (clock skew).

Falsability:
    A PASS finding becomes FAIL iff `(now - observed_at)` exceeds
    stale_after_days.
    A FAIL finding becomes PASS iff `observed_at >= (now - stale_after_days)`.
    A clock-skew FAIL becomes PASS iff `observed_at <= now`.

The falsation block carries the exact threshold ISO so the report is
self-contained.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional

from inspector.evidence import Evidence
from inspector.rule import Finding, Rule
from inspector import __version__ as INSPECTOR_VERSION


DEFAULT_STALE_AFTER_DAYS = 90


@dataclass(frozen=True)
class StaleEntityRule:
    """stale_entity rule — conforms to inspector.rule.Rule protocol."""

    id: str = "stale_entity"
    version: str = "0.1.0"
    consumes_api: tuple = ("cmdb_get", "cmdb_engine_info")
    consumes_entities: tuple = ("all",)

    def evaluate(
        self,
        api,
        policy: dict,
        now: datetime,
        entity_ids: Optional[Iterable[str]] = None,
    ) -> Iterable[Finding]:
        """Run the rule over `entity_ids` (or all entities if None).

        `api` must expose `cmdb_get` and `cmdb_engine_info` (verified
        through consumes_api declaration). Other public-API functions
        may be used if the rule's consumes_api is updated.
        """
        if entity_ids is None:
            entity_ids = [e["id"] for e in api.cmdb_list()]

        stale_after_days = int(policy.get("stale_after_days", DEFAULT_STALE_AFTER_DAYS))
        engine = api.cmdb_engine_info()

        for eid in sorted(entity_ids):
            ev_raw = api.cmdb_get(eid)
            evidence = _evidence_from_result(
                ev_raw, eid, engine.get("dataset_hash"), INSPECTOR_VERSION,
            )
            observed_at = evidence.observed_at
            if observed_at is None:
                yield Finding(
                    rule_id=self.id,
                    entity_id=eid,
                    status="skipped",
                    severity="info",
                    message="No observed_at — cannot evaluate freshness.",
                    evidence=evidence,
                    policy={"rule_id": self.id, "stale_after_days": stale_after_days,
                            "reference_now": now.isoformat()},
                    falsation={"observed_at_must_be_set": True},
                )
                continue
            yield self._judge(evidence, stale_after_days, now)

    def _judge(self, evidence: Evidence, stale_after_days: int, now: datetime) -> Finding:
        observed = _parse_iso(evidence.observed_at)
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        age_days = (now - observed).total_seconds() / 86400.0

        if age_days < 0:
            return Finding(
                rule_id=self.id,
                entity_id=evidence.entity_id,
                status="fail",
                severity="warning",
                message=f"Evidence timestamp is in the future relative to "
                        f"reference clock (age = {age_days:.2f} days, negative). "
                        f"Possible clock skew.",
                evidence=evidence,
                policy={"rule_id": self.id, "stale_after_days": stale_after_days,
                        "reference_now": now.isoformat()},
                falsation={
                    "observed_at_must_be_le": now.isoformat(),
                    "current_observed_at": evidence.observed_at,
                    "age_must_be_non_negative": True,
                },
            )

        is_stale = age_days > stale_after_days
        stamp_threshold = now.timestamp() - (stale_after_days * 86400)
        threshold_iso = (
            datetime.fromtimestamp(stamp_threshold, tz=timezone.utc).isoformat()
        )
        return Finding(
            rule_id=self.id,
            entity_id=evidence.entity_id,
            status="fail" if is_stale else "pass",
            severity="warning" if is_stale else "info",
            message=f"Evidence age = {age_days:.2f} days "
                    f"(threshold = {stale_after_days} days).",
            evidence=evidence,
            policy={"rule_id": self.id, "stale_after_days": stale_after_days,
                    "reference_now": now.isoformat()},
            falsation={
                "observed_at_must_be_greater_or_equal": threshold_iso,
                "current_observed_at": evidence.observed_at,
                "age_must_be_le": f"{stale_after_days} days",
            },
        )


def _parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def _evidence_from_result(result, entity_id: str, dataset_hash, inspector_version) -> Evidence:
    if not result.exists or result.evidence is None:
        return Evidence(
            api="cmdb_get",
            entity_id=entity_id,
            observed_at=None,
            age_seconds=None,
            ttl_seconds=None,
            confidence_level=None,
            confidence_basis=[],
            entity_hash=None,
            dataset_hash=dataset_hash,
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
        dataset_hash=dataset_hash,
        inspector_version=inspector_version,
    )


# Module-level singleton — every consumer of this rule uses the same
# instance. Saves constructing it per call.
RULE = StaleEntityRule()
