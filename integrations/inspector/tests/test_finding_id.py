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
