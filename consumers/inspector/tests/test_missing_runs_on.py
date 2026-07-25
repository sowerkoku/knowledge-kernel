"""Tests for missing_runs_on rule."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from inspector.rules.missing_runs_on import (
    RULE as MISSING_RUNS_RULE,
    MissingRunsOnRule,
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


def _ns_result(*, exists, evidence, entity=None):
    return SimpleNamespace(
        exists=exists,
        evidence=evidence,
        entity=entity if entity is not None else (object() if exists else None),
    )


class _StubAPI:
    """cmdb_list(kind=...) filters by kind; cmdb_get returns per eid."""

    def __init__(self, world):
        # world: dict entity_id -> {"kind": "...", "relations": [...]}
        self._world = world
        self.calls = {
            "cmdb_list": 0, "cmdb_get": 0, "cmdb_engine_info": 0,
        }

    def cmdb_engine_info(self):
        self.calls["cmdb_engine_info"] += 1
        return {"dataset_hash": "stub", "generation": 1}

    def cmdb_list(self, kind=None):
        self.calls["cmdb_list"] += 1
        out = []
        for eid, info in self._world.items():
            if kind is None or info["kind"] == kind:
                out.append({"id": eid, "kind": info["kind"]})
        return out

    def cmdb_get(self, entity_id):
        self.calls["cmdb_get"] += 1
        info = self._world.get(entity_id)
        if info is None:
            return _ns_result(exists=False, evidence=None, entity=None)
        ev = _StubEvidence(observed_at="2026-07-24T08:00:00+00:00")
        entity = SimpleNamespace(relations=info.get("relations", []))
        return _ns_result(exists=True, evidence=ev, entity=entity)


def test_protocol_conformance():
    r = MissingRunsOnRule()
    assert r.id == "missing_runs_on"
    assert r.version == "0.1.0"
    for fn in r.consumes_api:
        assert fn.startswith("cmdb_")
    assert callable(r.evaluate)


def test_pass_when_runs_on_present():
    api = _StubAPI({
        "app-1": {"kind": "software", "relations": [
            {"type": "runs_on", "target": "server-1"}
        ]},
    })
    findings = list(MISSING_RUNS_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["app-1"],
    ))
    assert findings[0].status == "pass"
    assert findings[0].severity == "info"


def test_fail_when_no_runs_on():
    api = _StubAPI({
        "app-1": {"kind": "software", "relations": [
            {"type": "uses", "target": "docker-stack-1"}
        ]},
    })
    findings = list(MISSING_RUNS_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["app-1"],
    ))
    assert findings[0].status == "fail"
    assert findings[0].severity == "warning"


def test_fail_when_empty_relations():
    api = _StubAPI({"app-1": {"kind": "software", "relations": []}})
    findings = list(MISSING_RUNS_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["app-1"],
    ))
    assert findings[0].status == "fail"


def test_falsation_for_fail_cites_current_relations():
    api = _StubAPI({
        "app-1": {"kind": "software", "relations": [
            {"type": "uses", "target": "docker"}
        ]},
    })
    findings = list(MISSING_RUNS_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["app-1"],
    ))
    f = findings[0]
    assert f.falsation["entity_must_have_relation_of_type"] == "runs_on"
    # The falsation records the *current* state (the relations we see).
    assert f.falsation["current_relations"] == [
        {"type": "uses", "target": "docker"}
    ]


def test_only_target_kinds_inspected():
    """If target_kinds=('software',), an 'agent' entity is not listed."""
    api = _StubAPI({
        "soft-1": {"kind": "software", "relations": []},
        "agent-1": {"kind": "agent", "relations": []},
    })
    findings = list(MISSING_RUNS_RULE.evaluate(
        api=api,
        policy={"target_kinds": ("software",)},
        now=FIXED_NOW,
    ))
    ids = [f.entity_id for f in findings]
    assert ids == ["soft-1"]


def test_unknown_target_kinds_rejected():
    """Empty target_kinds must raise — don't silently run on everything."""
    api = _StubAPI({})
    try:
        list(MISSING_RUNS_RULE.evaluate(
            api=api, policy={"target_kinds": ()}, now=FIXED_NOW,
        ))
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_skipped_when_entity_doesnt_exist():
    api = _StubAPI({})
    findings = list(MISSING_RUNS_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["ghost"],
    ))
    assert findings[0].status == "skipped"


def test_consumes_api_only_invokes_declared_apis_when_explicit_ids():
    """When entity_ids is provided, the rule does not call cmdb_list."""
    api = _StubAPI({
        "app-1": {"kind": "software", "relations": []},
    })
    list(MISSING_RUNS_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["app-1"],
    ))
    assert api.calls["cmdb_list"] == 0
    assert api.calls["cmdb_get"] >= 1


def test_consumes_api_invokes_list_when_entity_ids_None():
    """When entity_ids is None, cmdb_list is required to filter by kind."""
    api = _StubAPI({
        "app-1": {"kind": "software", "relations": []},
    })
    list(MISSING_RUNS_RULE.evaluate(api=api, policy={}, now=FIXED_NOW))
    assert api.calls["cmdb_list"] >= 1
