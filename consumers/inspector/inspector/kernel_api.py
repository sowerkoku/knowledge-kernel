"""KernelAPI — minimal wrapper exposing ONLY the public surface of the
Knowledge Kernel.

The Inspector imports cmdb.api.* exclusively through this object. No
other module in inspector.* imports from cmdb.* directly. This makes
the "only the public API" constraint structural: if a rule ever needs
something not exposed here, that itself is an evidence point — either
the rule is wrong or the public surface should grow.

Each attribute is callable and forwards to the corresponding
cmdb.api function. Adds no behaviour of its own.
"""

from __future__ import annotations

from cmdb.api import (
    cmdb_exists,
    cmdb_get,
    cmdb_search,
    cmdb_list,
    cmdb_validate,
    cmdb_impact,
    cmdb_assert,
    cmdb_context,
    cmdb_engine_info,
    cmdb_stats,
)


PUBLIC_FUNCTIONS = (
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
)


class KernelAPI:
    """Thin façade over the public Knowledge Kernel API.

    No state. No caching. No transformation. A rule that calls
    api.cmdb_get(x) is calling the same function as the one imported
    from cmdb.api.cmdb_get. Use this object as the inspector-side
    handle to the Kernel.
    """

    cmdb_exists = staticmethod(cmdb_exists)
    cmdb_get = staticmethod(cmdb_get)
    cmdb_search = staticmethod(cmdb_search)
    cmdb_list = staticmethod(cmdb_list)
    cmdb_validate = staticmethod(cmdb_validate)
    cmdb_impact = staticmethod(cmdb_impact)
    cmdb_assert = staticmethod(cmdb_assert)
    cmdb_context = staticmethod(cmdb_context)
    cmdb_engine_info = staticmethod(cmdb_engine_info)
    cmdb_stats = staticmethod(cmdb_stats)


def default_api() -> KernelAPI:
    """Return a default KernelAPI facade."""
    return KernelAPI()
