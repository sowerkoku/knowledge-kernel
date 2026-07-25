"""Tests for low_confidence_entity rule.

Mirrors test_inspector.py style: synthetic API stub, fixed policy,
fixed `now`. Six invariants:

  1. Protocol conformance
  2. PASS when confidence >= minimum
  3. FAIL when confidence < minimum
  4. Policy change flips result
  5. Unknown minimum is rejected (bad policy -> explicit error)
  6. Skipped when no evidence present
"""

from __future__ import annotations

from datetime import datetime, timezone

from inspector.rules.low_confidence_entity import (
    RULE as LOW_CONF_RULE,
    LowConfidenceEntityRule,
)


FIXED_NOW = datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc)


class _StubEvidence:
    """Stand-in for Kernel evidence. Only the fields we read."""

    def __init__(self, *, observed_at, confidence_level):
        self.observed_at = observed_at
        cls = confidence_level
        if cls is not None:
            class _L:
                def __init__(self, name): self.name = name
            self.confidence_level = _L(cls)
        else:
            self.confidence_level = None
        self.confidence_basis = []
        self.ttl_seconds = None
        self.entity_hash = "deadbeef"
        self._age = 0.0

    def age_seconds(self):
        return self._age


def _result(*, observed_at=None, confidence_level=None):
    """Build a stand-in for the result of api.cmdb_get(eid).

    Pass observed_at=None to mean "no evidence present".
    Mirrors Kernel semantics: exists=True; evidence=None/Real; entity
    populated only when evidence is present.
    """
    from types import SimpleNamespace
    if observed_at is None:
        return SimpleNamespace(exists=True, evidence=None, entity=None)
    return SimpleNamespace(
        exists=True,
        evidence=_StubEvidence(
            observed_at=observed_at, confidence_level=confidence_level,
        ),
        entity=object(),
    )


class _StubAPI:
    """Records each call so we can verify Rule consumes only declared api.

    `observations_by_eid` maps entity_id to a dict with optional
    keys: observed_at, confidence_level.
    """

    def __init__(self, observations_by_eid):
        self._obs = observations_by_eid
        self.calls = {"cmdb_get": 0, "cmdb_list": 0, "cmdb_engine_info": 0}

    def cmdb_engine_info(self):
        self.calls["cmdb_engine_info"] += 1
        return {"dataset_hash": "stub-hash", "generation": 1}

    def cmdb_get(self, entity_id):
        self.calls["cmdb_get"] += 1
        cfg = self._obs.get(entity_id, {})
        return _result(
            observed_at=cfg.get("observed_at", "2026-07-24T08:00:00+00:00"),
            confidence_level=cfg.get("confidence_level", "MEDIUM"),
        )

    def cmdb_list(self):
        self.calls["cmdb_list"] += 1
        return [{"id": eid} for eid in self._obs.keys()]


def test_protocol_conformance():
    r = LowConfidenceEntityRule()
    assert r.id == "low_confidence_entity"
    assert r.version == "0.1.0"
    for fn in r.consumes_api:
        assert fn.startswith("cmdb_")
    assert callable(r.evaluate)


def test_pass_cases_at_minimum_or_above():
    api = _StubAPI({
        "e-high":   {"confidence_level": "HIGH"},
        "e-medium": {"confidence_level": "MEDIUM"},
    })
    findings = list(LOW_CONF_RULE.evaluate(
        api=api, policy={"minimum_confidence": "MEDIUM"}, now=FIXED_NOW,
    ))
    by_id = {f.entity_id: f for f in findings}
    assert by_id["e-high"].status == "pass"
    assert by_id["e-medium"].status == "pass"


def test_fail_when_below_minimum():
    api = _StubAPI({
        "e-low":     {"confidence_level": "LOW"},
        "e-unknown": {"confidence_level": "UNKNOWN"},
    })
    findings = list(LOW_CONF_RULE.evaluate(
        api=api, policy={"minimum_confidence": "MEDIUM"}, now=FIXED_NOW,
    ))
    by_id = {f.entity_id: f for f in findings}
    assert by_id["e-low"].status == "fail"
    assert by_id["e-low"].severity == "warning"
    assert by_id["e-unknown"].status == "fail"


def test_policy_changes_result():
    api = _StubAPI({"e-medium": {"confidence_level": "MEDIUM"}})
    findings_loose = list(LOW_CONF_RULE.evaluate(
        api=api, policy={"minimum_confidence": "LOW"}, now=FIXED_NOW,
    ))
    findings_strict = list(LOW_CONF_RULE.evaluate(
        api=api, policy={"minimum_confidence": "HIGH"}, now=FIXED_NOW,
    ))
    assert findings_loose[0].status == "pass"
    assert findings_strict[0].status == "fail"


def test_unknown_minimum_is_rejected():
    api = _StubAPI({"e-ok": {"confidence_level": "HIGH"}})
    try:
        list(LOW_CONF_RULE.evaluate(
            api=api, policy={"minimum_confidence": "VERY_HIGH"}, now=FIXED_NOW,
        ))
        raised = False
    except ValueError:
        raised = True
    assert raised, "Invalid policy must raise ValueError, not silently pass."


def test_skipped_when_no_evidence():
    api = _StubAPI({"e-no-evidence": {"observed_at": None}})
    findings = list(LOW_CONF_RULE.evaluate(
        api=api, policy={"minimum_confidence": "MEDIUM"}, now=FIXED_NOW,
    ))
    assert findings[0].status == "skipped"


def test_finding_has_falsation_for_pass_and_fail():
    api = _StubAPI({
        "e-pass": {"confidence_level": "HIGH"},
        "e-fail": {"confidence_level": "LOW"},
    })
    findings = list(LOW_CONF_RULE.evaluate(
        api=api, policy={"minimum_confidence": "MEDIUM"}, now=FIXED_NOW,
    ))
    by_id = {f.entity_id: f for f in findings}
    assert "pass_condition" in by_id["e-pass"].falsation
    assert "confidence_level_must_be_in" in by_id["e-fail"].falsation


def test_consumes_api_match_actual_calls():
    api = _StubAPI({"e-high": {"confidence_level": "HIGH"}})
    list(LOW_CONF_RULE.evaluate(
        api=api, policy={"minimum_confidence": "MEDIUM"}, now=FIXED_NOW,
    ))
    used = {k for k, v in api.calls.items() if v > 0}
    for fn in used:
        assert fn in LOW_CONF_RULE.consumes_api
