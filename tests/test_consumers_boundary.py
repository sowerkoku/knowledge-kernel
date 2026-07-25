"""Consumers/ boundary tests.

Verifies that the `consumers/` layer does not depend on any specific
external platform or framework. Enforces the architectural rule that
consumers/ and integrations/ are different layers:

  knowledge-kernel/
    kernel/         <- the model
    consumers/      <- native consumers of the public API
    integrations/   <- adapters to specific platforms

If a component in consumers/ needs to import from a specific platform
or framework, it is no longer a consumer — it is an integration.
"""

from __future__ import annotations

import ast
from pathlib import Path

# The platform catalogue is the canonical source of truth. Boundary
# tests read from it; tooling reads from it; scaffolding reads from it.
# See platforms.py for the entry point.
from platforms import PLATFORM_BOUNDARIES, by_package as _platform_by_package

# Set views used by individual assertions below.
PLATFORM_PACKAGES = frozenset(p.package for p in PLATFORM_BOUNDARIES)

CONSUMERS_ROOT = Path(__file__).resolve().parent.parent.parent / "consumers"
_REPO_ROOT = CONSUMERS_ROOT.parent


def _walk_python_files(root: Path):
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if "/tests/" in str(path):
            continue
        yield path


def _imports_in_file(path: Path) -> list[str]:
    ext = ast.parse(path.read_text(), filename=str(path))
    names: list[str] = []
    for node in ast.walk(ext):
        if isinstance(node, ast.Import):
            for n in node.names:
                names.append(n.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.append(node.module)
    return names


def test_consumers_dont_import_platform_packages():
    """consumers/ must not depend on a specific platform."""
    root = CONSUMERS_ROOT
    offenders: list[tuple[str, str, list[str]]] = []

    for py_path in _walk_python_files(root):
        for imp in _imports_in_file(py_path):
            top = imp.split(".")[0]
            if top in PLATFORM_PACKAGES:
                rel = py_path.relative_to(_REPO_ROOT)
                offender_loc = _platform_by_package(top).location
                offenders.append((str(rel), imp, [offender_loc]))

    if offenders:
        msgs = [f"{f}: imports {m} ({e[0]})" for f, m, e in offenders]
        raise AssertionError(
            "consumers/ depends on a platform:\n  " + "\n  ".join(msgs)
            + "\nComponents that need a platform belong in integrations/."
        )


def test_consumers_dont_import_integrations_layer():
    """consumers/ must not import from integrations/ siblings.

    A consumer of the Kernel API is framework-agnostic. It must not
    reach into a specific integration to share utilities either.
    """
    root = CONSUMERS_ROOT
    offenders: list[tuple[str, str]] = []

    for py_path in _walk_python_files(root):
        if "/tests/" in str(py_path):
            continue
        for imp in _imports_in_file(py_path):
            if imp.startswith("integrations."):
                rel = py_path.relative_to(_REPO_ROOT)
                offenders.append((str(rel), imp))

    if offenders:
        msgs = [f"{f}: imports {m}" for f, m in offenders]
        raise AssertionError(
            "consumers/ imports from integrations/:\n  "
            + "\n  ".join(msgs)
            + "\nMove shared utilities to kernel/ or keep them in consumers/."
        )


def test_consumers_are_platform_agnostic():
    """consumers/* must not depend on a specific platform or framework.

    The rule is not "stdlib only". The rule is "platform-agnostic".
    Third-party libraries (pydantic, networkx, click, rich, etc.)
    are fine. Imports from known platforms (hermes, openclaw...),
    or from the integrations/ layer itself, are not.

    When this test fails, the offending component must move from
    consumers/ to integrations/, where platform-specific code belongs.
    """
    root = CONSUMERS_ROOT
    offenders: list[tuple[str, str, str]] = []

    for py_path in _walk_python_files(root):
        module_name = py_path.stem
        rel = py_path.relative_to(_REPO_ROOT)
        for imp in _imports_in_file(py_path):
            top = imp.split(".")[0]
            # Platform packages: tracked in PLATFORM_PACKAGES via the
            # canonical catalogue in platforms.py.
            if top in PLATFORM_PACKAGES:
                entry = _platform_by_package(top)
                offenders.append((str(rel), imp, entry.location))
                continue
            # Cross-layer bleed: anything from integrations/ is suspect.
            if imp.startswith("integrations."):
                offenders.append((str(rel), imp, "integrations layer"))
                continue
            # Anything else: stdlib, third-party, kernel public API.
            # All allowed.

    if offenders:
        msgs = [f"{f}: imports {m} ({why})" for f, m, why in offenders]
        raise AssertionError(
            "consumers/ depends on a platform:\n  "
            + "\n  ".join(msgs)
            + "\nMove the offending module to integrations/, or keep it "
            + "in consumers/ without the platform dependency."
        )


def test_platform_packages_registry_is_tracking():
    """Sanity check: PLATFORM_PACKAGES tracks at least one well-known name.

    If this test ever becomes the only warning that someone added a
    new platform-aware consumer without extending the registry, it
    is still better than silent drift.
    """
    assert "hermes" in PLATFORM_PACKAGES
    assert "kernel" not in PLATFORM_PACKAGES, (
        "kernel is not a platform; remove from registry."
    )
