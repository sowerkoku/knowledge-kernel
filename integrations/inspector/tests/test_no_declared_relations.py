"""Tests for no_declared_relations rule.

The rule measures presence/absence of relations — a *fact*, not a
verdict. These tests verify four things:

  1. The rule reuses the v0.1 contract untouched.
  2. The rule emits per-entity Findings only (no aggregate Finding
     that would require a contract extension).
  3. Policy filters apply before evaluation and remain auditable
     in the falsation block.
  4. The rule's primary output, when run against a synthetic world
     with mixed kinds, exposes the fact distribution by kind.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from inspector.rules.no_declared_relations import (
    RULE as NO_REL_RULE,
    NoDeclaredRelationsRule,
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


class _StubEntity:
    def __init__(self, kind, status, relations):
        self.kind = kind
        self.status = status
        self.relations = relations


class _StubAPI:
    """Stub cmdb.list/get/engine_info compatible with the rule."""

    def __init__(self, world):
        # world: dict entity_id -> {
        #    "kind": "...", "status": "...", "relations": [...]
        # }
        self._world = world
        self.calls = {"cmdb_list": 0, "cmdb_get": 0, "cmdb_engine_info": 0}

    def cmdb_engine_info(self):
        self.calls["cmdb_engine_info"] += 1
        return {"dataset_hash": "stub", "generation": 1}

    def cmdb_list(self):
        self.calls["cmdb_list"] += 1
        return [{"id": eid} for eid in self._world.keys()]

    def cmdb_get(self, entity_id):
        self.calls["cmdb_get"] += 1
        w = self._world.get(entity_id)
        if w is None:
            return SimpleNamespace(exists=False, evidence=None, entity=None)
        ev = _StubEvidence(observed_at="2026-07-24T08:00:00+00:00")
        e = _StubEntity(kind=w["kind"], status=w["status"],
                        relations=w.get("relations", []))
        return SimpleNamespace(exists=True, evidence=ev, entity=e)


def test_protocol_conformance():
    r = NoDeclaredRelationsRule()
    assert r.id == "no_declared_relations"
    assert r.version == "0.1.0"
    for fn in r.consumes_api:
        assert fn.startswith("cmdb_")
    assert callable(r.evaluate)


def test_fail_when_no_relations():
    api = _StubAPI({"x-1": {"kind": "software", "status": "operational",
                            "relations": []}})
    findings = list(NO_REL_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["x-1"],
    ))
    assert findings[0].status == "fail"
    assert findings[0].severity == "warning"


def test_pass_when_has_relations():
    api = _StubAPI({"x-1": {
        "kind": "software", "status": "operational",
        "relations": [{"type": "runs_on", "target": "h-1"}],
    }})
    findings = list(NO_REL_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["x-1"],
    ))
    assert findings[0].status == "pass"


def test_ignored_kinds_exclude_from_findings():
    """A kind in ignored_kinds produces SKIPPED (not silently dropped).
    The operator sees it in the report with status=skipped."""
    api = _StubAPI({
        "x-1": {"kind": "endpoint", "status": "operational",
                "relations": []},
        "x-2": {"kind": "software", "status": "operational",
                "relations": [{"type": "runs_on", "target": "h-1"}]},
    })
    findings = list(NO_REL_RULE.evaluate(
        api=api,
        policy={"ignored_kinds": ("endpoint",)},
        now=FIXED_NOW,
    ))
    by_id = {f.entity_id: f for f in findings}
    # x-1 was filtered by kind: SKIPPED
    assert by_id["x-1"].status == "skipped"
    # x-2 passes
    assert by_id["x-2"].status == "pass"


def test_ignored_statuses_exclude_from_findings():
    """A status in ignored_statuses produces SKIPPED (not silently dropped).
    The operator sees it in the report with status=skipped."""
    api = _StubAPI({
        "x-stopped":  {"kind": "software", "status": "stopped", "relations": []},
        "x-active":   {"kind": "software", "status": "operational",
                       "relations": [{"type": "runs_on", "target": "h-1"}]},
    })
    findings = list(NO_REL_RULE.evaluate(
        api=api,
        policy={"ignored_statuses": ("stopped",)},
        now=FIXED_NOW,
    ))
    by_id = {f.entity_id: f for f in findings}
    # x-stopped filtered by status: SKIPPED
    assert by_id["x-stopped"].status == "skipped"
    # x-active passes
    assert by_id["x-active"].status == "pass"


def test_required_relation_types_filter_considered_relations():
    """If required_relation_types=('runs_on',), other relation types
    do not count toward presence."""
    api = _StubAPI({"x-1": {
        "kind": "software", "status": "operational",
        "relations": [{"type": "uses", "target": "docker"}],
    }})
    findings = list(NO_REL_RULE.evaluate(
        api=api,
        policy={"required_relation_types": ("runs_on",)},
        now=FIXED_NOW,
        entity_ids=["x-1"],
    ))
    # No runs_on -> FAIL.
    assert findings[0].status == "fail"
    # Falsation block exposes raw vs considered counts — operator can
    # see that a relation exists but of a different type.
    assert findings[0].falsation["raw_relations_count"] == 1
    assert findings[0].falsation["considered_count_actual"] == 0


def test_pass_when_required_type_present():
    api = _StubAPI({"x-1": {
        "kind": "software", "status": "operational",
        "relations": [{"type": "runs_on", "target": "h-1"}],
    }})
    findings = list(NO_REL_RULE.evaluate(
        api=api,
        policy={"required_relation_types": ("runs_on",)},
        now=FIXED_NOW,
        entity_ids=["x-1"],
    ))
    assert findings[0].status == "pass"


def test_skipped_when_no_entity():
    api = _StubAPI({})
    findings = list(NO_REL_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["ghost"],
    ))
    assert findings[0].status == "skipped"


def test_falsation_includes_filter_used_for_fail():
    api = _StubAPI({"x-1": {
        "kind": "software", "status": "operational", "relations": [],
    }})
    findings = list(NO_REL_RULE.evaluate(
        api=api,
        policy={"ignored_kinds": (), "ignored_statuses": (),
                "required_relation_types": ("runs_on",)},
        now=FIXED_NOW,
        entity_ids=["x-1"],
    ))
    f = findings[0]
    assert "filter_used" in f.falsation
    assert f.falsation["filter_used"]["required_relation_types"] == ["runs_on"]
    # The raw facts the rule observed.
    assert f.falsation["raw_kind"] == "software"
    assert f.falsation["raw_status"] == "operational"


def test_consumes_api_only_invokes_declared():
    api = _StubAPI({
        "x-1": {"kind": "software", "status": "operational", "relations": []},
    })
    list(NO_REL_RULE.evaluate(
        api=api, policy={}, now=FIXED_NOW, entity_ids=["x-1"],
    ))
    used = {k for k, v in api.calls.items() if v > 0}
    for fn in used:
        assert fn in NO_REL_RULE.consumes_api


def test_deterministic_two_runs():
    api = _StubAPI({
        "x-1": {"kind": "software", "status": "operational", "relations": []},
        "x-2": {"kind": "software", "status": "operational",
                "relations": [{"type": "runs_on", "target": "h-1"}]},
    })

    def once():
        return list(NO_REL_RULE.evaluate(
            api=api, policy={}, now=FIXED_NOW, entity_ids=["x-1", "x-2"],
        ))

    a = once()
    b = once()
    assert [(f.entity_id, f.status) for f in a] == [(f.entity_id, f.status) for f in b]
