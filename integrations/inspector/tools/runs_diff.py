"""Dataset-plane utility: runs_diff.

Compares two Inspector runs and reports what changed between them.
This is a *tool*, not part of the Inspector contract (Rule, Finding,
KernelAPI, Report). It lives in the Dataset measurement plane.

What it answers:
  appeared          — findings in current that were not in previous
  disappeared       — findings in previous that are not in current
  stable            — findings present in both runs (same identity)
  changed           — findings present in both but with a different
                      observable property

Changed findings are further classified:
  severity_changed  — same finding, different severity
  status_changed    — same finding, different status
  policy_changed    — same finding, different policy snapshot
  evidence_changed  — same finding, different evidence hash

Two identifiers per finding:
  finding_key  = (rule_id, entity_id)              — logical identity
  finding_id   = (rule_id, entity_id, status,
                  evidence.entity_hash)             — observation identity

Use finding_key to answer: "is this same problem still present?"
Use finding_id  to answer: "is this exactly the same observation?"

No metrics (DIR, FP, FC) are produced here. Those emerge only after
observing recurring questions across real run pairs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal

Run = dict  # a deserialised Report.to_dict()


# ---------------------------------------------------------------------------
# Finding identifiers
# ---------------------------------------------------------------------------

def finding_key(finding: dict) -> str:
    """Logical identity: survives across status/evidence changes.

    Two findings with the same finding_key represent the same
    (rule, entity) pair — the same underlying problem, even if its
    status or evidence has changed.
    """
    return f"{finding['rule_id']}|{finding['entity_id']}"


def finding_id(finding: dict) -> str:
    """Observation identity: (rule_id, entity_id, status, evidence_hash).

    Two findings with the same finding_id are the exact same
    observation. If either status or entity_hash differs, the
    finding_id differs.
    """
    parts = [
        finding["rule_id"],
        finding["entity_id"],
        finding["status"],
    ]
    ev = finding.get("evidence")
    if ev and ev.get("entity_hash") is not None:
        parts.append(str(ev["entity_hash"]))
    digest = _sha16("|".join(parts))
    return f"{finding['rule_id']}|{finding['entity_id']}|{digest}"


def _sha16(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Change categorisation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FindingDelta:
    finding_id: str       # observation identity
    finding_key: str      # logical identity
    field: str            # which property changed ('status', 'severity', ...)
    previous: object
    current: object

    def describe(self) -> str:
        return (
            f"{self.finding_key}: {self.field} "
            f"{self.previous!r} → {self.current!r}"
        )


@dataclass
class RunDiff:
    appeared: list[str] = field(default_factory=list)      # finding_ids
    disappeared: list[str] = field(default_factory=list)   # finding_ids
    stable: list[str] = field(default_factory=list)        # finding_ids (by finding_id)
    changed: list[FindingDelta] = field(default_factory=list)
    severity_changed: list[str] = field(default_factory=list)   # finding_keys
    status_changed: list[str] = field(default_factory=list)     # finding_keys
    policy_changed: list[str] = field(default_factory=list)      # finding_keys
    evidence_changed: list[str] = field(default_factory=list)    # finding_keys

    def to_dict(self) -> dict:
        return {
            "appeared": sorted(self.appeared),
            "disappeared": sorted(self.disappeared),
            "stable": sorted(self.stable),
            "changed_count": len(self.changed),
            "severity_changed": sorted(self.severity_changed),
            "status_changed": sorted(self.status_changed),
            "policy_changed": sorted(self.policy_changed),
            "evidence_changed": sorted(self.evidence_changed),
        }

    def changed_by_key(self) -> dict[str, FindingDelta]:
        return {d.finding_key: d for d in self.changed}


# ---------------------------------------------------------------------------
# Core diff algorithm
# ---------------------------------------------------------------------------

def diff_runs(previous: Run, current: Run) -> RunDiff:
    """Compare two Inspector runs and return a structured diff.

    Args:
        previous: Deserialised Report (from Report.to_dict()).
        current:  Deserialised Report (from Report.to_dict()).

    Returns:
        RunDiff with findings-level comparison.

    Both runs MUST have the same policy version for policy_changed
    to be meaningful; if they differ, all findings are tagged
    policy_changed=True.
    """
    # Index by finding_key (logical identity) so that the same entity
    # with different status/evidence is recognized as the SAME finding.
    prev = _index_findings_by_key(previous.get("findings", []))
    curr = _index_findings_by_key(current.get("findings", []))

    prev_keys = set(prev)
    curr_keys = set(curr)

    result = RunDiff()
    # finding_id values for appeared/disappeared: use finding_id from current
    result.appeared = sorted(
        finding_id(curr[k]) for k in sorted(curr_keys - prev_keys)
    )
    result.disappeared = sorted(
        finding_id(prev[k]) for k in sorted(prev_keys - curr_keys)
    )
    result.stable = sorted(
        finding_id(prev[k]) for k in sorted(prev_keys & curr_keys)
    )

    for key in prev_keys & curr_keys:
        pi = prev[key]
        ci = curr[key]
        _categorise_change(pi, ci, result)

    return result


def _index_findings_by_key(findings: list[dict]) -> dict[str, dict]:
    """Index findings by finding_key (logical identity)."""
    return {finding_key(f): f for f in findings}


def _index_findings(findings: list[dict]) -> dict[str, dict]:
    """Index findings by finding_id (observation identity)."""
    return {finding_id(f): f for f in findings}


def _categorise_change(prev_f: dict, curr_f: dict, result: RunDiff):
    """Inspect a stable finding_key and record any property changes."""
    fkey = finding_key(prev_f)
    fid = finding_id(curr_f)

    deltas: list[FindingDelta] = []

    for field in ("status", "severity"):
        pv = prev_f.get(field)
        cv = curr_f.get(field)
        if pv != cv:
            deltas.append(FindingDelta(
                finding_id=fid,
                finding_key=fkey,
                field=field,
                previous=pv,
                current=cv,
            ))

    # Policy comparison: compare the policy snapshot dicts
    pp = prev_f.get("policy", {})
    cp = curr_f.get("policy", {})
    if pp != cp:
        deltas.append(FindingDelta(
            finding_id=fid,
            finding_key=fkey,
            field="policy",
            previous=pp,
            current=cp,
        ))

    # Evidence hash comparison
    peh = prev_f.get("evidence", {}).get("entity_hash")
    ceh = curr_f.get("evidence", {}).get("entity_hash")
    if peh != ceh:
        deltas.append(FindingDelta(
            finding_id=fid,
            finding_key=fkey,
            field="evidence_hash",
            previous=peh,
            current=ceh,
        ))

    if deltas:
        result.changed.extend(deltas)
        for d in deltas:
            if d.field == "severity":
                result.severity_changed.append(d.finding_key)
            elif d.field == "status":
                result.status_changed.append(d.finding_key)
            elif d.field == "policy":
                result.policy_changed.append(d.finding_key)
            elif d.field in ("evidence_hash",):
                result.evidence_changed.append(d.finding_key)


# ---------------------------------------------------------------------------
# Persistence helpers (tools only — not Inspector contract)
# ---------------------------------------------------------------------------

def load_run(path: str | Path) -> Run:
    """Load a serialised run from a JSON file."""
    with open(path) as fh:
        return json.load(fh)


def save_run(run: Run, path: str | Path) -> None:
    """Persist a run to a JSON file."""
    with open(path, "w") as fh:
        json.dump(run, fh, indent=2, default=str)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: Iterable[str] | None = None) -> RunDiff:
    """CLI for runs_diff.

    Usage:
        python -m inspector.tools.runs_diff previous.json current.json

    Output (to stdout):
        appeared, disappeared, stable counts and full listing.
        changed findings with field-level diff.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare two Inspector runs and report what changed."
    )
    parser.add_argument("previous", help="Path to previous run JSON")
    parser.add_argument("current",  help="Path to current run JSON")
    parser.add_argument("--quiet", action="store_true", help="Show only counts")
    args = parser.parse_args(argv)

    prev = load_run(args.previous)
    curr = load_run(args.current)

    d = diff_runs(prev, curr)

    if not args.quiet:
        print(f"Dataset A: {prev.get('generated_at', '?')}")
        print(f"Dataset B: {curr.get('generated_at', '?')}")
        print()
        print(f"  Stable:       {len(d.stable)}")
        print(f"  Appeared:     {len(d.appeared)}")
        print(f"  Disappeared:  {len(d.disappeared)}")
        print(f"  Changed:      {len(d.changed)}")
        print()
        for label, items in [
            ("severity_changed", d.severity_changed),
            ("status_changed",   d.status_changed),
            ("policy_changed",   d.policy_changed),
            ("evidence_changed", d.evidence_changed),
        ]:
            if items:
                print(f"  {label}:")
                for k in sorted(items):
                    print(f"    {k}")

    return d


if __name__ == "__main__":
    main()