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

__all__ = [
    # Query API (agent-facing)
    "cmdb_exists",   # Check existence before asserting
    "cmdb_get",      # Get entity with facts + relations
    "cmdb_search",   # Search entities
    "cmdb_list",     # List by kind/status
    "cmdb_impact",   # Impact analysis (NEW)
    "cmdb_validate", # Validate CMDB health
    
    # Migration
    "cmdb_migrate_dry_run",
    "cmdb_migrate_apply",
    
    # Low-level utilities
    "load_entities",
    "load_entities_with_paths",
]