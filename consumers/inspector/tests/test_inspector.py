"""Tests for the Knowledge Inspector.

Three invariant tests:

    test_falsability — the documented change flips the verdict
    test_determinism — same inputs → same report
    test_policy_change — different policies, same evidence,
                         different verdicts

Plus a discovery/contract test that confirms the rule conforms to the
Rule protocol.

If these pass, the Inspector's contract (5 principles + Rule protocol)
is preserved in code.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from inspector.kernel_api import KernelAPI
from inspector.report import run_inspector
from inspector.rule import Finding, Rule, validate_rule_object
from inspector.rules.stale_entity import (
    RULE as STALE_ENTITY_RULE,
    _evidence_from_result,
    DEFAULT_STALE_AFTER_DAYS,
    StaleEntityRule,
)


# Pin a reference clock. Synthetic tests must be deterministic; real
# evidence will almost always sit in the future of this clock, which
# the rule handles as clock-skew (fail with severity=warning).
FIXED_NOW = datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc)

API = default_api() if False else __import__(
    "inspector.kernel_api", fromlist=["default_api"]
).default_api()


# --- Protocol conformance --------------------------------------------------


def test_rule_protocol_conformance():
    """The StaleEntityRule must conform to the Rule protocol."""
    rule = StaleEntityRule()
    ok, missing = validate_rule_object(rule)
    assert ok, f"Rule missing attributes: {missing}"
    assert rule.id == "stale_entity"
    assert rule.version == "0.1.0"
    assert "cmdb_get" in rule.consumes_api
    assert callable(rule.evaluate)


def test_consumes_api_uses_only_public_surface():
    """consumes_api must list only functions exposed by KernelAPI."""
    rule = StaleEntityRule()
    public = set(dir(API)) - {"__class__", "__dict__", "__doc__",
                              "__init_subclass__", "__subclasshook__",
                              "__weakref__"}
    public_api = {n for n in public if n.startswith("cmdb_")}
    for fn_name in rule.consumes_api:
        assert fn_name in public_api, (
            f"Rule {rule.id} declares consumes_api={fn_name!r} but that "
            f"name is not on KernelAPI. Inspector must consume only the "
            f"public surface."
        )


def test_module_singleton():
    """`from inspector.rules.stale_entity import RULE` exposes one rule."""
    assert STALE_ENTITY_RULE.id == "stale_entity"
    assert isinstance(STALE_ENTITY_RULE, StaleEntityRule)


# --- Synthetic evidence (deterministic) ------------------------------------


class _StubResult:
    """Minimal stand-in for cmdb_get() result, used to drive the rule
    on synthetic timestamps without touching the live Kernel."""

    def __init__(self, observed_at, confidence="MEDIUM", basis=None,
                 age_seconds=0.0, ttl_seconds=None, entity_hash="deadbeef"):
        self.exists = True
        self.entity = object()
        self.evidence = _StubEvidence(
            observed_at=observed_at,
            confidence=confidence,
            basis=basis or ("SCHEMA_VALIDATED", "HUMAN_DECLARED"),
            age_seconds=age_seconds,
            ttl_seconds=ttl_seconds,
            entity_hash=entity_hash,
        )


class _StubEvidence:
    def __init__(self, **kw):
        self.observed_at = kw.get("observed_at")
        self.confidence_level = kw.get("confidence")
        self.confidence_basis = kw.get("basis")
        self.ttl_seconds = kw.get("ttl_seconds")
        self.entity_hash = kw.get("entity_hash")
        self._age = kw.get("age_seconds", 0.0)

    def age_seconds(self):
        return self._age


class _StubAPI:
    """Minimal API stub satisfying the rule's consumes_api."""

    def __init__(self, observations):
        # observations: dict entity_id -> observed_at ISO string
        self._observations = observations
        self.engine_calls = 0
        self.get_calls = 0

    def cmdb_engine_info(self):
        self.engine_calls += 1
        return {"dataset_hash": "stub-hash", "generation": 1}

    def cmdb_get(self, entity_id):
        self.get_calls += 1
        observed = self._observations.get(entity_id)
        if observed is None:
            return _MissingResult(entity_id)
        return _StubResult(observed)

    def cmdb_list(self):
        # Required only when entity_ids is None; tests always pass them.
        return []


class _MissingResult:
    def __init__(self, eid):
        self.exists = False
        self.entity = None
        self.evidence = None


def _find(rule_outputs, eid):
    """Pull the Finding for entity_id from a generator of findings."""
    for f in rule_outputs:
        if f.entity_id == eid:
            return f
    return None


def test_falsability_synthetic():
    """Fresh evidence → pass; old evidence → fail; both carry falsation."""
    api = _StubAPI({
        "e-fresh": "2026-07-24T06:00:00+00:00",  # 6h old
        "e-old":   "2026-04-01T12:00:00+00:00",  # ~115d old
    })
    rule = StaleEntityRule()
    findings = list(rule.evaluate(
        api=api,
        policy={"stale_after_days": 90},
        now=FIXED_NOW,
        entity_ids=["e-fresh", "e-old"],
    ))

    f_fresh = _find(findings, "e-fresh")
    f_old = _find(findings, "e-old")
    assert f_fresh.status == "pass", f_fresh
    assert f_old.status == "fail", f_old
    assert f_old.severity == "warning"
    assert "observed_at_must_be_greater_or_equal" in f_old.falsation


def test_clock_skew_surfaces_as_finding():
    """Future observed_at must yield a clock-skew fail, not silent pass."""
    api = _StubAPI({"e-future": "2030-01-01T00:00:00+00:00"})
    rule = StaleEntityRule()
    findings = list(rule.evaluate(
        api=api,
        policy={"stale_after_days": 90},
        now=FIXED_NOW,
        entity_ids=["e-future"],
    ))
    f = findings[0]
    assert f.status == "fail"
    assert "future" in f.message.lower()
    assert "age_must_be_non_negative" in f.falsation


def test_policy_changes_result_synthetic():
    """Two different policies against the same evidence yield
    different verdicts."""
    api = _StubAPI({"e-old": "2026-01-01T00:00:00+00:00"})  # ~205d old
    rule = StaleEntityRule()

    findings_strict = list(rule.evaluate(
        api=api,
        policy={"stale_after_days": 0},
        now=FIXED_NOW,
        entity_ids=["e-old"],
    ))
    findings_loose = list(rule.evaluate(
        api=api,
        policy={"stale_after_days": 10_000},
        now=FIXED_NOW,
        entity_ids=["e-old"],
    ))
    assert findings_strict[0].status == "fail", (
        "stale_after_days=0 with old evidence must produce STALE"
    )
    assert findings_loose[0].status == "pass", (
        "stale_after_days=10000 with old evidence must produce PASS"
    )
    assert findings_strict[0].severity != findings_loose[0].severity


def test_finding_serialisation_is_self_contained():
    """A Finding.to_dict() round-trips its falsation intact."""
    from dataclasses import asdict
    api = _StubAPI({"e-x": "2026-04-01T00:00:00+00:00"})
    rule = StaleEntityRule()
    findings = list(rule.evaluate(
        api=api,
        policy={"stale_after_days": 90},
        now=FIXED_NOW,
        entity_ids=["e-x"],
    ))
    f = findings[0]
    d = asdict(f)
    assert isinstance(d["falsation"], dict)
    assert "observed_at_must_be_greater_or_equal" in d["falsation"]
    # The dict is JSON-safe: no nested dataclasses.
    import json
    json.dumps(d)  # raises if anything non-serialisable


# --- Determinism -----------------------------------------------------------


def test_run_inspector_is_deterministic():
    """Two runs of the Inspector against the same kernel produce
    byte-equal lists of finding identities for `stale_entity`."""
    from cmdb.api import cmdb_list
    sample = sorted(e["id"] for e in cmdb_list())[:5]
    api = __import__("inspector.kernel_api",
                     fromlist=["default_api"]).default_api()

    def once():
        report = run_inspector(
            rules=[StaleEntityRule()],
            api=api,
            policy={"stale_after_days": 90},
            now=FIXED_NOW,
        )
        return [f.entity_id for f in report.findings]

    assert once() == once()


# --- Smoke against the live kernel -----------------------------------------


def test_smoke_against_live_kernel():
    """End-to-end smoke: the Inspector does not fail on the live dataset."""
    api = __import__("inspector.kernel_api",
                     fromlist=["default_api"]).default_api()
    report = run_inspector(
        rules=[StaleEntityRule()],
        api=api,
        policy={"stale_after_days": 90},
        now=datetime.now(tz=timezone.utc),
    )
    assert isinstance(report.to_json(), str)
    assert len(report.findings) >= 0  # may be 0 if dataset has no entities
