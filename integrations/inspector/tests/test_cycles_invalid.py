"""Tests for cycles_invalid rule.

The experiment behind this rule is documented in CONTRACT.md:
"¿La implementación real confirma que la API pública es suficiente
sin introducir acoplamientos ocultos?". The tests verify four
properties:

  1. cmdb_impact(.*)'s shape is what the rule expects.
  2. No internal kernel modules are pulled in.
  3. False/positive decisions: self-reachable -> FAIL; not reachable
     -> PASS; missing evidence -> SKIPPED; non-existent entity ->
     SKIPPED.
  4. Falsation depends on the observable condition, not on the
     specific edge to break.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from inspector.rules.cycles_invalid import (
    RULE as CYCLES_RULE,
    CyclesInvalidRule,
)


FIXED_NOW = datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc)


class _StubEvidence:
    def __init__(self, observed_at):
        self.observed_at = observed_at
        self.confidence_level = None
        self.confidence_basis = []
        self.ttl_seconds = None
        self.entity_hash = "deadbeef"

    def age_seconds(self):
        return 0.0


class _StubAPI:
    """Backs the rule with controllable impact responses."""

    def __init__(self, *, worlds):
        # worlds: dict entity_id -> {
        #    "exists": bool,
        #    "transitive": list[str],    # entries for i_depend_on.transitive
        #    "evidence": bool,            # True -> entity has evidence
        # }
        self._worlds = worlds
        self.calls = {
            "cmdb_list": 0, "cmdb_impact": 0,
            "cmdb_get": 0, "cmdb_engine_info": 0,
        }

    def cmdb_engine_info(self):
        self.calls["cmdb_engine_info"] += 1
        return {"dataset_hash": "stub", "generation": 1}

    def cmdb_list(self):
        self.calls["cmdb_list"] += 1
        return [{"id": eid} for eid in self._worlds.keys()]

    def cmdb_get(self, entity_id):
        self.calls["cmdb_get"] += 1
        world = self._worlds.get(entity_id)
        if world is None or not world.get("evidence", True):
            return SimpleNamespace(exists=False, evidence=None, entity=None)
        ev = _StubEvidence(observed_at="2026-07-24T08:00:00+00:00")
        return SimpleNamespace(exists=True, evidence=ev, entity=object())

    def cmdb_impact(self, entity_id):
        self.calls["cmdb_impact"] += 1
        world = self._worlds.get(entity_id, {"exists": False})
        if not world.get("exists", False):
            return {"exists": False}
        return {
            "exists": True,
            "i_depend_on": {
                "direct": world.get("direct", []),
                "transitive": [
                    {"id": x} for x in world.get("transitive", [])
                ],
            },
        }


def test_protocol_conformance():
    r = CyclesInvalidRule()
    assert r.id == "cycles_invalid"
    assert r.version == "0.1.0"
    for fn in r.consumes_api:
        assert fn.startswith("cmdb_")
    assert callable(r.evaluate)


def test_fail_when_self_reachable():
    """Entity X appears in its own transitive set -> FAIL."""
    api = _StubAPI(worlds={
        "X": {"exists": True, "transitive": ["X", "Y"]},
    })
    findings = list(CYCLES_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["X"],
    ))
    assert findings[0].status == "fail"
    assert findings[0].severity == "warning"


def test_pass_when_not_self_reachable():
    """Entity X's transitive set does NOT include X -> PASS."""
    api = _StubAPI(worlds={
        "X": {"exists": True, "transitive": ["Y", "Z"]},
    })
    findings = list(CYCLES_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["X"],
    ))
    assert findings[0].status == "pass"
    assert findings[0].severity == "info"


def test_pass_when_no_transitive_deps():
    api = _StubAPI(worlds={"X": {"exists": True, "transitive": []}})
    findings = list(CYCLES_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["X"],
    ))
    assert findings[0].status == "pass"


def test_skipped_when_no_evidence():
    """cmdb_get returns evidence=None -> SKIPPED."""
    api = _StubAPI(worlds={
        "X": {"exists": True, "evidence": False, "transitive": ["X"]},
    })
    findings = list(CYCLES_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["X"],
    ))
    assert findings[0].status == "skipped"


def test_skipped_when_no_entity():
    """cmdb_impact.exists=False -> SKIPPED."""
    api = _StubAPI(worlds={"X": {"exists": False}})
    findings = list(CYCLES_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["X"],
    ))
    assert findings[0].status == "skipped"


def test_falsation_cites_observable_condition_not_repair():
    """Falsation refers to the observable state, no prescriptive
    'remove edge A-B' guidance."""
    api = _StubAPI(worlds={
        "X": {"exists": True, "transitive": ["X"]},
    })
    findings = list(CYCLES_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["X"],
    ))
    f = findings[0]
    assert "entity_not_present_in" in f.falsation
    assert "self_reachable" in f.falsation
    bad_keys = ("remove", "break", "suggest")
    for k in f.falsation:
        assert k not in bad_keys, (
            f"Falsation key {k!r} is prescriptive; should be observable."
        )


def test_consumes_api_only_invokes_declared():
    api = _StubAPI(worlds={
        "X": {"exists": True, "transitive": []},
        "Y": {"exists": True, "transitive": []},
    })
    list(CYCLES_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["X"],
    ))
    used = {k for k, v in api.calls.items() if v > 0}
    for fn in used:
        assert fn in CYCLES_RULE.consumes_api, (
            f"Rule called {fn!r} which it does not declare."
        )


def test_deterministic_for_two_runs():
    api = _StubAPI(worlds={
        "X": {"exists": True, "transitive": ["X"]},
        "Y": {"exists": True, "transitive": []},
    })
    r1 = [(f.entity_id, f.status, f.severity) for f in CYCLES_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["X", "Y"],
    )]
    r2 = [(f.entity_id, f.status, f.severity) for f in CYCLES_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["X", "Y"],
    )]
    assert r1 == r2
