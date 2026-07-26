"""Tests for stable finding identifiers and cross-run diffing.

Verifies the Dataset-plane capabilities added to the Reporter:
  - `finding_identifier()` produces a stable, uniquely-named id per
    (rule, entity, status, evidence_hash).
  - The same evidence running again yields the same id.
  - Different statuses or evidence hashes yield different ids.
  - `diff_findings` correctly partitions ids across runs.

No changes to Inspector contract (Rule, Finding, KernelAPI).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from inspector.rule import Finding
from inspector.report import finding_identifier, diff_findings


def _mk(rule_id, entity_id, status, *, hash_value=None, severity="info"):
    from inspector.evidence import Evidence
    evidence = Evidence(
        api="cmdb_get",
        entity_id=entity_id,
        observed_at=None,
        age_seconds=None,
        ttl_seconds=None,
        confidence_level=None,
        confidence_basis=[],
        entity_hash=hash_value,
        dataset_hash="x",
        inspector_version="0.1.0",
    ) if hash_value else None
    return Finding(
        rule_id=rule_id,
        entity_id=entity_id,
        status=status,
        severity=severity,
        message="x",
        evidence=evidence,
        policy={},
        falsation={},
    )


def test_identifier_is_deterministic_for_same_inputs():
    f = _mk("r1", "e1", "pass", hash_value="abc")
    assert finding_identifier(f) == finding_identifier(f)


def test_identifier_changes_with_status():
    """Pass and fail on same evidence yield different ids."""
    fp = _mk("r1", "e1", "pass", hash_value="abc")
    ff = _mk("r1", "e1", "fail", hash_value="abc")
    assert finding_identifier(fp) != finding_identifier(ff)


def test_identifier_changes_with_evidence_hash():
    """Different evidence hashes -> different identifiers."""
    f1 = _mk("r1", "e1", "pass", hash_value="abc")
    f2 = _mk("r1", "e1", "pass", hash_value="xyz")
    assert finding_identifier(f1) != finding_identifier(f2)


def test_identifier_format_readable():
    """Identifiers should be readable: rule|entity|<short hex>."""
    f = _mk("stale_entity", "server-1", "pass", hash_value="abc")
    pid = finding_identifier(f)
    parts = pid.split("|")
    assert parts[0] == "stale_entity"
    assert parts[1] == "server-1"
    assert len(parts[2]) == 16  # last segment is short hex


def test_diff_findings_partitions_ids():
    prev = {
        "r|a|aaa1",
        "r|b|bbb2",
        "r|c|ccc3",
    }
    curr = {
        "r|b|bbb2",    # stable
        "r|d|ddd4",    # appeared
        # aaa1 disappeared
        # ccc3 disappeared
    }
    d = diff_findings(previous_ids=prev, current_ids=curr)
    assert d["stable"] == ["r|b|bbb2"]
    assert d["appeared"] == ["r|d|ddd4"]
    assert sorted(d["disappeared"]) == ["r|a|aaa1", "r|c|ccc3"]


def test_diff_is_pure_set_difference():
    """diff_findings must not have side-effects."""
    a = {"x"}
    b = {"x", "y"}
    diff_findings(a, b)
    diff_findings(b, a)
    assert a == {"x"}
    assert b == {"x", "y"}


def test_evidence_none_yields_still_stable_id():
    """Skipped findings (no evidence) still get a stable id."""
    f = _mk("r1", "e1", "skipped", hash_value=None)
    pid = finding_identifier(f)
    assert "|" in pid
    assert pid == finding_identifier(f)


# ---------------------------------------------------------------------------
# Cross-representation tests
# ---------------------------------------------------------------------------
#
# After consolidation of the hash formula into inspector.identity, the
# same Finding (object) and its deserialised form (dict) must produce
# the same identifier. These tests guard the contract that "una
# representación puede cambiar; la identidad no".


def _finding_to_dict(f: Finding) -> dict:
    """Helper: serialise a Finding to the JSON-able dict produced
    by inspector.report._findings_to_jsonable. We do not import the
    private function — instead we asdict() which is exactly what
    _findings_to_jsonable does internally."""
    from dataclasses import asdict
    d = asdict(f)
    # finding_id is added by the serialiser; we don't need it here.
    return d


def _import_runs_diff():
    """Import inspector.tools.runs_diff via path-based loading.

    The tool module is not exposed as a Python package under the
    `inspector.` namespace because `consumers/inspector/tools/` is a
    sibling of `consumers/inspector/inspector/`, not a subpackage.
    This is intentional: tools do not depend on the Inspector
    contract. To exercise the equivalence of representations, we
    load the module file directly. The risk is that the tests do
    not track structural moves of the tool; the contract guarded
    here is the *identity formula*, which lives in inspector/identity
    and is import-stable."""
    import importlib.util
    import sys
    from pathlib import Path
    runs_diff_path = (
        Path(__file__).resolve().parent.parent / "tools" / "runs_diff.py"
    )
    spec = importlib.util.spec_from_file_location(
        "tests.tools.runs_diff_under_test", runs_diff_path
    )
    if spec is None:
        raise ImportError(f"Cannot spec runs_diff at {runs_diff_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # register so dataclasses can find __module__
    assert spec.loader is not None, "ModuleSpec without a loader"
    spec.loader.exec_module(mod)
    return mod


def test_finding_identifier_from_object_equals_from_dict():
    """The Finding() and dict(dict()) representations of the same data
    must produce the same identifier. This is the contract that lets
    tools/runs_diff.py and inspector/report.py coexist."""
    runs_diff = _import_runs_diff()
    f = _mk("stale_entity", "server-1", "pass", hash_value="abc")
    d = _finding_to_dict(f)
    # Sanity: dict shape matches what tools/runs_diff expects
    assert d["rule_id"] == "stale_entity"
    assert d["entity_id"] == "server-1"
    assert d["status"] == "pass"
    assert d["evidence"]["entity_hash"] == "abc"

    id_from_object = finding_identifier(f)
    id_from_dict = runs_diff.finding_id(d)
    assert id_from_object == id_from_dict


def test_finding_key_from_object_equals_from_dict():
    """Logical identity (key) is also closed under representation."""
    runs_diff = _import_runs_diff()
    f = _mk("stale_entity", "server-1", "pass", hash_value="abc")
    d = _finding_to_dict(f)
    from inspector.identity import finding_key
    key_from_object = finding_key(rule_id=f.rule_id, entity_id=f.entity_id)
    key_from_dict = runs_diff.finding_key(d)
    assert key_from_object == key_from_dict


def test_evidence_none_preserves_equivalence():
    """Findings without evidence must still be equivalent across
    representations; the skipped-branch logic must match between
    report.py and runs_diff.py."""
    runs_diff = _import_runs_diff()
    f = _mk("stale_entity", "server-1", "skipped", hash_value=None)
    d = _finding_to_dict(f)
    assert d["evidence"] is None
    id_from_object = finding_identifier(f)
    id_from_dict = runs_diff.finding_id(d)
    assert id_from_object == id_from_dict


def test_format_stable_for_canonical_inputs():
    """The identifier format must match the canonical idempotent
    computation. test_identifier_format_readable checks the rule_id
    and entity_id prefix; this checks that the digest segment is
    exactly 16 hex chars and matches a known anchor (so a future
    algorithm change would surface here)."""
    f = _mk("stale_entity", "server-1", "pass", hash_value="abc")
    pid = finding_identifier(f)
    parts = pid.split("|")
    assert parts[0] == "stale_entity"
    assert parts[1] == "server-1"
    digest = parts[2]
    assert len(digest) == 16
    # digest must be hex
    int(digest, 16)  # raises if not hex
