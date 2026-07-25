"""Rule — protocol and helpers for Inspector rules.

A Rule is the *only* unit of business logic in the Inspector. Each rule
must implement `evaluate()` and produce Finding objects whose falsation
field is already populated.

The infrastructure concerns (JSON, CLI, timestamps, repetition,
metrics) live elsewhere. A rule never touches them. The `consumes_api`
tuple is declarative: it lists the cmdb.api functions the rule relies
on, so the Inspector can verify that the rule consumes only the public
surface and so any future change to the Kernel API can be checked
against every rule's declaration.

Why a Protocol and not a base class:
    - Rules are *independent*. They should not share state or hidden
      helpers through inheritance.
    - The Inspector should be able to discover rules from filesystem
      (drop-in folder of rule modules).
    - Multiple concrete rules are easier to reason about when each is
      a typed object that conforms to a protocol, rather than a class
      hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Optional, Protocol, runtime_checkable

from inspector.evidence import Evidence


@dataclass(frozen=True)
class Finding:
    """One falsable result. Severities: info, warning, fail."""

    rule_id: str
    entity_id: str
    status: str            # 'fail' | 'pass' | 'skipped'
    severity: str          # 'info' | 'warning' | 'fail'
    message: str
    evidence: Optional[Evidence]
    policy: dict
    falsation: dict = field(default_factory=dict)
    """Concrete data change that would flip this finding's status.

    Keys are rule-specific but always serialisable (str, int, float,
    list, dict). The Inspector never reads this — the consumer (human
    or downstream tool) is the one who decides what to do with the
    falsation. Attaching it to the Finding keeps the JSON report
    self-contained.
    """


@runtime_checkable
class Rule(Protocol):
    """One rule of the Inspector.

    Each rule contributes:
        id                stable identifier (e.g. 'stale_entity')
        version           rule version (semantic; bump on breaking policy)
        consumes_api      tuple of cmdb.api function names the rule
                          depends on; used by the Inspector to verify
                          it consumes only the public surface
        consumes_entities select the entities this rule cares about:
                            ("all",) | ("by_kind", "<kind>") |
                            ("by_status", "<status>") |
                            ("by_id", "<id-or-glob>")
        evaluate          run the rule; produce findings
    """

    id: str
    version: str
    consumes_api: tuple[str, ...]
    consumes_entities: tuple

    def evaluate(
        self,
        api: Any,
        policy: dict,
        now: datetime,
    ) -> Iterable[Finding]:
        ...


def validate_rule_object(obj: Any) -> tuple[bool, list[str]]:
    """Verify a rule object conforms to the Rule protocol.

    Returns (ok, missing_attributes). Pure runtime check; the typing
    system already enforces most of this at import time. This helper is
    for the Inspector's rule discovery layer.
    """
    if not isinstance(obj, Rule):
        return False, ["object does not conform to Rule protocol"]
    missing = []
    for attr in ("id", "version", "consumes_api", "consumes_entities", "evaluate"):
        if not hasattr(obj, attr):
            missing.append(attr)
    return (len(missing) == 0), missing
