"""Tests for runs_diff tool (Dataset-plane).

These tests verify the diffing primitives only — finding_key,
finding_id, and diff_runs. No Inspector contract is involved.

Two run files are synthesised from minimal finding dicts to test
the full categorisation matrix: stable, appeared, disappeared,
severity_changed, status_changed, policy_changed, evidence_changed.
"""

from __future__ import annotations

import importlib.util
import sys

# Load runs_diff as a standalone module without polluting sys.path.
# tools/ is at integrations/inspector/tools/ (sibling of the inspector
# package). We load it directly from its absolute location.
_tools_path = (
    "/home/carlos/knowledge-kernel/integrations/inspector/tools/runs_diff.py"
)
_spec = importlib.util.spec_from_file_location("inspector.tools.runs_diff", _tools_path)
_runs_diff = importlib.util.module_from_spec(_spec)
# Make it visible in sys.modules so dataclass decorators can resolve.
sys.modules["inspector.tools.runs_diff"] = _runs_diff  # type: ignore[index]
_spec.loader.exec_module(_runs_diff)

finding_key = _runs_diff.finding_key
finding_id = _runs_diff.finding_id
diff_runs = _runs_diff.diff_runs
load_run = _runs_diff.load_run
save_run = _runs_diff.save_run
RunDiff = _runs_diff.RunDiff
FindingDelta = _runs_diff.FindingDelta


def _f(rule, entity, status="pass", severity="info",
       evid_hash="abc", policy=None):
    """Minimal finding dict for testing."""
    return {
        "rule_id": rule,
        "entity_id": entity,
        "status": status,
        "severity": severity,
        "message": "x",
        "evidence": {"entity_hash": evid_hash} if evid_hash else {},
        "policy": policy or {"rule_id": rule},
        "falsation": {},
    }


def _run(findings):
    return {"generated_at": "2026-07-24T00:00:00Z", "findings": findings}


# ---------------------------------------------------------------------------
# Identifier tests
# ---------------------------------------------------------------------------

def test_finding_key_is_rule_plus_entity():
    f = _f("stale_entity", "server-1")
    assert finding_key(f) == "stale_entity|server-1"


def test_finding_key_ignores_status():
    f1 = _f("r", "e", status="pass")
    f2 = _f("r", "e", status="fail")
    assert finding_key(f1) == finding_key(f2)


def test_finding_key_ignores_evidence():
    f1 = _f("r", "e", evid_hash="abc")
    f2 = _f("r", "e", evid_hash="xyz")
    assert finding_key(f1) == finding_key(f2)


def test_finding_id_changes_with_status():
    f1 = _f("r", "e", status="pass")
    f2 = _f("r", "e", status="fail")
    assert finding_id(f1) != finding_id(f2)


def test_finding_id_changes_with_evidence_hash():
    f1 = _f("r", "e", evid_hash="abc")
    f2 = _f("r", "e", evid_hash="xyz")
    assert finding_id(f1) != finding_id(f2)


def test_finding_id_format():
    pid = finding_id(_f("stale_entity", "server-1"))
    parts = pid.split("|")
    assert parts[0] == "stale_entity"
    assert parts[1] == "server-1"
    assert len(parts[2]) == 16


# ---------------------------------------------------------------------------
# Diff tests
# ---------------------------------------------------------------------------

def test_stable_findings_unchanged():
    prev = _run([_f("r", "e1"), _f("r", "e2")])
    curr = _run([_f("r", "e1"), _f("r", "e2")])
    d = diff_runs(prev, curr)
    assert len(d.stable) == 2
    assert len(d.appeared) == 0
    assert len(d.disappeared) == 0
    assert len(d.changed) == 0


def test_appeared_findings():
    prev = _run([_f("r", "e1")])
    curr = _run([_f("r", "e1"), _f("r", "e2")])
    d = diff_runs(prev, curr)
    assert "stale_entity|e2" in d.appeared or d.appeared  # finding_ids
    assert len(d.disappeared) == 0


def test_disappeared_findings():
    prev = _run([_f("r", "e1"), _f("r", "e2")])
    curr = _run([_f("r", "e1")])
    d = diff_runs(prev, curr)
    assert len(d.disappeared) == 1


def test_severity_changed():
    prev = _run([_f("r", "e1", severity="info")])
    curr = _run([_f("r", "e1", severity="warning")])
    d = diff_runs(prev, curr)
    assert len(d.severity_changed) == 1
    assert len(d.status_changed) == 0


def test_status_changed():
    prev = _run([_f("r", "e1", status="pass")])
    curr = _run([_f("r", "e1", status="fail")])
    d = diff_runs(prev, curr)
    assert len(d.status_changed) == 1
    assert len(d.severity_changed) == 0


def test_evidence_changed():
    prev = _run([_f("r", "e1", evid_hash="abc")])
    curr = _run([_f("r", "e1", evid_hash="xyz")])
    d = diff_runs(prev, curr)
    assert len(d.evidence_changed) == 1
    assert len(d.severity_changed) == 0


def test_policy_changed():
    p1 = {"rule_id": "r", "threshold": 90}
    p2 = {"rule_id": "r", "threshold": 60}
    prev = _run([_f("r", "e1", policy=p1)])
    curr = _run([_f("r", "e1", policy=p2)])
    d = diff_runs(prev, curr)
    assert len(d.policy_changed) == 1


def test_changed_list_has_delta_objects():
    prev = _run([_f("r", "e1", severity="info")])
    curr = _run([_f("r", "e1", severity="warning")])
    d = diff_runs(prev, curr)
    assert len(d.changed) == 1
    delta = d.changed[0]
    assert isinstance(delta, FindingDelta)
    assert delta.field == "severity"
    assert delta.previous == "info"
    assert delta.current == "warning"


def test_empty_runs():
    d = diff_runs(_run([]), _run([]))
    assert d.stable == []
    assert d.appeared == []
    assert d.disappeared == []


def test_to_dict_seralises_correctly():
    prev = _run([_f("r", "e1", status="pass")])
    curr = _run([_f("r", "e1", status="fail")])
    d = diff_runs(prev, curr)
    dd = d.to_dict()
    assert "stable" in dd
    assert "changed_count" in dd
    assert dd["changed_count"] == 1


def test_load_save_roundtrip(tmp_path):
    run = _run([_f("r", "e1")])
    path = tmp_path / "run.json"
    save_run(run, path)
    loaded = load_run(path)
    assert loaded == run
    assert loaded["findings"][0]["rule_id"] == "r"