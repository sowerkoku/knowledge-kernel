"""
Get Dataset Validation Report

Returns the full health of the Knowledge Kernel dataset: errors, warnings,
and entity/relation statistics. Use this BEFORE committing YAML changes,
before pushes, or as part of a cron health job.

Agent usage:
  Use this for health checks before/after dataset changes:
  - "Is the dataset valid right now?"
  - "Are there any malformed entities?"
  - "What are the warnings to review before committing?"
  - "How many entities per domain/kind/status exist?"

Returns:
  {
    "valid": true|false,
    "errors": [{"entity_id": ..., "field": ..., "message": ...}, ...],
    "warnings": [{"entity_id": ..., "field": ..., "message": ...}, ...],
    "stats": {
      "total": 54,
      "by_domain": {"infrastructure": 17, "software": 31, "organization": 6},
      "by_kind": {"asset": 7, "automation": 2, "endpoint": 10, "agent": 6, "software": 29},
      "by_status": {"operational": 53, "deprecated": 1}
    }
  }

This is heavier than cmdb_stats() — it walks every entity and surfaces
schema/relation issues. Use cmdb_stats() for cheap composition queries.
"""

import os
import sys
from pathlib import Path

# Ensure repo is importable
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

# Set data dir
os.environ.setdefault("CMDB_DATA_DIR", str(Path.home() / "knowledge" / "knowledge-kernel"))

from cmdb.api import cmdb_validate


def cmdb_validate_wrapper() -> dict:
    """
    Run a full health check on the Knowledge Kernel dataset.

    Use for:
    - Pre-commit validation
    - Pre-push validation
    - Cron health jobs
    - Post-edit verification (after cmdb_reload)

    Returns:
        dict with keys:
        - valid: bool — overall pass/fail
        - errors: list[dict] — schema/structural errors (dataset invalid if any)
        - warnings: list[dict] — soft issues (dataset valid but review recommended)
        - stats: dict — entity breakdown by domain/kind/status

    Behavioral rule:
    - ALWAYS run this after writing or editing YAML entities
    - Non-zero errors mean the dataset must not be trusted until fixed
    - Warnings do not block, but should be triaged
    """
    return cmdb_validate()


if __name__ == "__main__":
    import json
    result = cmdb_validate_wrapper()
    print(json.dumps(result, indent=2, default=str))
