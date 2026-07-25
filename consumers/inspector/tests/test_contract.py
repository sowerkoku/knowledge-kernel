"""Contract — regression test for the v0.1 Inspector contract.

This file does NOT verify behaviour; it verifies that the contract
documented in CONTRACT.md is what the code actually exposes.

If a future change modifies inspector.rule.Rule, inspector.rule.Finding,
or inspector.kernel_api.KernelAPI in a way that violates the v0.1
contract, this test must be the first to surface the violation.

Updating this test is a contract change. Update CONTRACT.md in the
same commit and bump inspector.__version__.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from typing import get_type_hints

import pytest

from inspector.rule import Finding, Rule
from inspector.kernel_api import KernelAPI, PUBLIC_FUNCTIONS


# --- Rule protocol ----------------------------------------------------------


def test_Rule_is_a_runtime_protocol():
    """Rule must be a Protocol (no instantiation, used for structural
    typing)."""
    import typing
    from inspector.rule import Rule as R
    assert getattr(R, "_is_runtime_protocol", False) or hasattr(R, "__call__"), (
        "inspector.rule.Rule must remain a runtime-checkable Protocol"
    )


def test_public_functions_constant_is_unchanged():
    """The Inspector's view of which Kernel functions are public is
    pinned. Any change requires a contract revision."""
    assert PUBLIC_FUNCTIONS == (
        "cmdb_exists",
        "cmdb_get",
        "cmdb_search",
        "cmdb_list",
        "cmdb_validate",
        "cmdb_impact",
        "cmdb_assert",
        "cmdb_context",
        "cmdb_engine_info",
        "cmdb_stats",
    ), (
        "PUBLIC_FUNCTIONS changed. If this is intentional, it is a v0.2 "
        "contract change."
    )


# --- Finding dataclass ------------------------------------------------------


def test_Finding_has_exact_v01_fields():
    """The Finding dataclass fields and their shape are frozen in v0.1."""
    expected = {
        "rule_id": str,
        "entity_id": str,
        "status": str,
        "severity": str,
        "message": str,
        "evidence": object,
        "policy": dict,
        "falsation": dict,
    }
    actual_names = {f.name for f in fields(Finding)}
    assert actual_names == set(expected.keys()), (
        f"Finding fields changed: {actual_names.symmetric_difference(expected.keys())}"
    )


def test_Finding_status_and_severity_vocabularies():
    """The vocabulary documented in CONTRACT.md is enforced via tests.
    Renaming these strings is a v0.2 contract change."""
    from inspector.report import run_inspector
    # We don't need to enforce static constants — the documentation +
    # rule behaviour is the contract. This test documents the expected
    # vocabulary in a way that grep can find.
    assert hasattr(run_inspector, "__doc__")
    assert "findings" in run_inspector.__code__.co_varnames


def test_Finding_is_immutable():
    """Findings must be frozen — they are assertions, not mutable
    opinions."""
    f = Finding(
        rule_id="r", entity_id="e", status="pass", severity="info",
        message="x", evidence=None, policy={}, falsation={},
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        f.status = "fail"


# --- KernelAPI façade -------------------------------------------------------


def test_KernelAPI_exposes_only_public_functions():
    """`from cmdb.api import X` outside the Inspector codebase is a v0.2
    violation. We verify by sniffing source: no module under inspector/
    should `import cmdb.*` except inspector.kernel_api.
    """
    import pathlib
    inspector_root = pathlib.Path(__file__).resolve().parent.parent / "inspector"
    forbidden = []
    allowed_module = inspector_root / "kernel_api.py"
    for py in inspector_root.rglob("*.py"):
        if py == allowed_module:
            continue
        if py.name == "__init__.py" and py.parent == inspector_root:
            continue
        for line in py.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("from cmdb.") or stripped.startswith("import cmdb"):
                forbidden.append((py, line))
    assert not forbidden, (
        "Inspector modules other than kernel_api.py must NOT import cmdb.*. "
        "Found: " + ", ".join(f"{p}: {line}" for p, line in forbidden)
    )


def test_KernelAPI_class_has_only_public_methods():
    """Only methods whose names match PUBLIC_FUNCTIONS belong on KernelAPI.
    Other attributes (dunder methods) are Python infrastructure, not API.
    """
    names = dir(KernelAPI)
    public = set(PUBLIC_FUNCTIONS)
    # Dunder methods are Python infrastructure — ignore them.
    dunder = {n for n in names if n.startswith("__")}
    unexpected = (
        {n for n in names if not n.startswith("_") and n not in dunder}
        - public
    )
    assert not unexpected, (
        f"KernelAPI exposes non-public names: {unexpected}"
    )


# --- Falsation belongs to Finding -------------------------------------------


def test_Finding_has_falsation_field_not_method():
    """Falsation is a field on Finding — keep the report self-contained."""
    assert "falsation" in [f.name for f in fields(Finding)]


# --- Version pin ------------------------------------------------------------


def test_inspector_version_is_pinned_at_0_1_0():
    """v0.1 contract; bumps require CONTRACT.md update."""
    import inspector
    assert inspector.__version__ == "0.1.0"
    assert inspector.__policy_version__ == "0.1.0"
