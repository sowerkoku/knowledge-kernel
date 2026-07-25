"""Inspector report — deterministic output of a run.

A report pins everything needed to reproduce the same findings:
dataset_hash, inspector_version, policy_version, generation, and the
parameters used. Any two runs with the same four inputs MUST produce
identical reports — identical findings, severities, falsation blocks.

Each rendered finding also carries a stable `finding_id`, derived
from the source rule, the affected entity, the current status, and
the evidence hash. The id does not change across reruns that yield
the same verdict on the same evidence, so it can be used to diff
runs over time.

Writes JSON via to_json(). Never writes to the Knowledge Kernel.
Never modifies the dataset.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Type

from inspector import __version__, __policy_version__
from inspector.kernel_api import KernelAPI, default_api
from inspector.rule import Finding, Rule


def finding_identifier(f: Finding) -> str:
    """Stable identifier for an emitted finding.

    Built from (rule_id, entity_id, status, evidence_hash). Two
    runs that produce the same rule's verdict on the same entity
    with the same evidence will receive the same identifier; that
    is the property the Dataset-plane analyses rely on.

    Skipped findings still receive an identifier so the report
    count is symmetric with the rule's covered-entities count.
    """
    parts: list[str] = []
    parts.append(f.rule_id)
    parts.append(f.entity_id)
    parts.append(f.status)
    if f.evidence is not None:
        eh = f.evidence.entity_hash
        if eh is not None:
            parts.append(str(eh))
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    # 16 hex chars = 64 bits — enough for collision-free inside one
    # dataset, short enough to be readable.
    return f"{f.rule_id}|{f.entity_id}|{digest[:16]}"


@dataclass(frozen=True)
class Report:
    generated_at: str
    inspector_version: str
    policy_version: str
    dataset_hash: str
    generation: int
    parameters: dict
    findings: tuple = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "inspector_version": self.inspector_version,
            "policy_version": self.policy_version,
            "dataset_hash": self.dataset_hash,
            "generation": self.generation,
            "parameters": self.parameters,
            "findings_count": len(self.findings),
            "findings": _findings_to_jsonable(self.findings),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def _findings_to_jsonable(findings: Iterable[Finding]) -> list:
    out = []
    for f in findings:
        d = asdict(f)
        d["finding_id"] = finding_identifier(f)
        out.append(d)
    return out


def run_inspector(
    rules: Iterable[Type[Rule] | Rule],
    *,
    api: KernelAPI | None = None,
    policy: dict | None = None,
    now: datetime | None = None,
) -> Report:
    """Run a set of rules against the Knowledge Kernel via the public API.

    Args:
        rules: Iterable of Rule classes (or instances) to run.
        api: KernelAPI facade. Defaults to a fresh instance exposing
             only public API functions.
        policy: Dict of policy parameters forwarded to each rule.
                The full dict is also pinned in the report.
        now: Override reference clock for reproducibility.
    """
    api = api or default_api()
    now = now or datetime.now(tz=timezone.utc)
    policy = policy or {}
    engine = api.cmdb_engine_info()

    findings: list[Finding] = []
    for rule_obj in rules:
        rule: Rule
        if isinstance(rule_obj, type):
            rule = rule_obj()
        else:
            rule = rule_obj
        # Verify rule consumes only declared public API.
        for fn_name in rule.consumes_api:
            if fn_name not in {n for n in dir(api) if not n.startswith("_")}:
                raise ValueError(
                    f"Rule {rule.id} declares consumes_api={fn_name!r} "
                    f"but this name is not exposed by KernelAPI."
                )
        for f in rule.evaluate(api=api, policy=policy, now=now):
            findings.append(f)

    return Report(
        generated_at=now.isoformat(),
        inspector_version=__version__,
        policy_version=__policy_version__,
        dataset_hash=str(engine.get("dataset_hash")),
        generation=int(engine.get("generation", 0)),
        parameters={"policy": policy, "now": now.isoformat()},
        findings=tuple(findings),
    )


def diff_findings(
    previous_ids: Iterable[str],
    current_ids: Iterable[str],
) -> dict:
    """Set-difference helpers for cross-run Findings comparison.

    Returns:
        {
          "appeared":   [<finding_id>, ...],   # in current, not in previous
          "disappeared": [<finding_id>, ...],  # in previous, not in current
          "stable":     [<finding_id>, ...],   # in both
        }

    This is the primitive for answering questions like:
      - "¿Este FAIL apareció hoy o ya existía?"
      - "¿Qué findings desaparecieron?"
    It is a Dataset-plane computation, not part of the Inspector
    contract.

    Re-runs of the same rule, same entity, same evidence, same
    verdict MUST yield the same identifier; if they don't, the
    policy or dataset has actually changed (use that signal).
    """
    prev = set(previous_ids)
    curr = set(current_ids)
    return {
        "appeared": sorted(curr - prev),
        "disappeared": sorted(prev - curr),
        "stable": sorted(prev & curr),
    }

