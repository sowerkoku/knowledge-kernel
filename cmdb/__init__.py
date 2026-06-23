# CMDB — Agent Configuration Management Database
# Factual memory layer for AI agents

from .validator import (
    cmdb_validate,
    load_entities,
    load_entities_with_paths,
)

from .impact import (
    cmdb_impact,
)

from .query import (
    cmdb_exists,
    cmdb_get,
    cmdb_search,
    cmdb_list,
)

from .migrator import (
    cmdb_migrate_dry_run,
    cmdb_migrate_apply,
)

from .assertions import (
    cmdb_assert,
    cmdb_context,
)

__all__ = [
    # Query API (agent-facing)
    "cmdb_exists",   # Check existence before asserting
    "cmdb_get",      # Get entity with facts + evidence
    "cmdb_search",   # Search entities
    "cmdb_list",     # List by kind/status
    "cmdb_assert",   # Binary validation for reasoning
    "cmdb_context",  # Pre-packaged agent context
    
    # Impact analysis
    "cmdb_impact",   # Dependency graph analysis
    
    # Migration
    "cmdb_migrate_dry_run",
    "cmdb_migrate_apply",
    
    # Validation
    "cmdb_validate",
    
    # Low-level utilities
    "load_entities",
    "load_entities_with_paths",
]