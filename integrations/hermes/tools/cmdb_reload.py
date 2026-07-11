"""
Reload Kernel Engine Indexes

Invalidates derived indexes and forces rebuild from canonical YAML store.

This is NOT a cache clear. The engine does not manage TTL, consistency, or
memoization. It builds deterministic derived views from YAML. After editing
YAML files, call this to invalidate those derived indexes so the next query
rebuilds them from the canonical YAML source.

Agent workflow:
  1. User edits a YAML file directly.
  2. Agent calls cmdb_reload() to invalidate derived indexes.
  3. Indexes rebuild immediately (~430ms cold start).
  4. Subsequent queries run against the new indexes (<1ms warm).

Returns an observable contract:
  {
    "reloaded": True,
    "entities": 36,
    "reload_ms": 428.7,
    "dataset_snapshot": "36@2026-07-11T21:07",
  }
"""

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure repo is importable
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

# Set data dir
os.environ.setdefault("CMDB_DATA_DIR", str(Path.home() / "knowledge" / "knowledge-kernel"))

from cmdb.engine import KernelEngine, clear_engine_cache


def _dataset_snapshot(engine: KernelEngine) -> str:
    """Build a human-readable snapshot label: count@ISO-uptime.

    Example: '36@2026-07-11T21:07'
    """
    try:
        all_entities = engine.get_all_entities()
        count = len(all_entities)
    except Exception:
        count = 0
    seed = getattr(engine, "_dataset_mtime", None)
    if isinstance(seed, (int, float)) and seed > 0:
        ts = datetime.fromtimestamp(seed, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M")
    else:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    return f"{count}@{ts}"


def cmdb_reload() -> dict:
    """
    Reload Kernel Engine indexes.

    Invalidates derived indexes and rebuilds them immediately from canonical
    YAML. Use this after editing YAML files directly.

    Returns:
        dict with observability keys: reloaded, entities, reload_ms, dataset_snapshot.
    """
    entities_dir = Path(os.environ.get("CMDB_DATA_DIR", Path.home() / "knowledge" / "knowledge-kernel"))

    t0 = time.perf_counter()

    # Step 1: Invalidate existing engine instance
    clear_engine_cache(entities_dir)

    # Step 2: Force immediate reload (not lazy) to get observable stats
    engine = KernelEngine.get_instance(entities_dir)
    engine.reload()

    reload_ms = round((time.perf_counter() - t0) * 1000, 2)

    dataset_snapshot = _dataset_snapshot(engine)

    # Count from snapshot label
    entity_count = int(dataset_snapshot.split("@")[0])

    return {
        "reloaded": True,
        "entities": entity_count,
        "reload_ms": reload_ms,
        "dataset_snapshot": dataset_snapshot,
    }


if __name__ == "__main__":
    import json
    result = cmdb_reload()
    print(json.dumps(result, indent=2))