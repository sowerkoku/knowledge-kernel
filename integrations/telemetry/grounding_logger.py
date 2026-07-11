"""
Telemetry for Knowledge Kernel — Query Events

Append-only JSONL logger for query-level telemetry.
Generates events automatically on every cmdb.* call.

Event types:
- query: API call metrics (KAR, latency, distribution)
- grounded_assertion: FGR tracking (agent-declared)

Output: ~/.hermes/telemetry/kernel/queries.jsonl
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict


# ---- Configuration --------------------------------------------------------

TELEMETRY_DIR = Path.home() / ".hermes" / "telemetry" / "kernel"
QUERIES_FILE = TELEMETRY_DIR / "queries.jsonl"
ASSERTIONS_FILE = TELEMETRY_DIR / "assertions.jsonl"


# ---- Event schemas --------------------------------------------------------

@dataclass
class QueryEvent:
    """Generated automatically on every cmdb.* call."""
    timestamp: str
    session_id: str
    agent_id: str
    api: str
    entity_id: Optional[str]
    kind_filter: Optional[str]
    facts_requested: int
    facts_found: int
    used_kernel: bool
    latency_ms: float
    schema_version: int = 1
    kernel_version: str = "L2.1"
    dataset_snapshot: Optional[str] = None

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass
class AssertionEvent:
    """Agent-declared assertion event."""
    timestamp: str
    session_id: str
    agent_id: str
    assertion: str
    fact_ids: List[str]
    schema_version: int = 1

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


# ---- Logger ---------------------------------------------------------------

def ensure_dirs() -> None:
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)


def get_session_id() -> str:
    """Get or create session ID from environment."""
    # Hermes sets HERMES_SESSION_ID; fallback to timestamp
    return os.environ.get("HERMES_SESSION_ID", datetime.now().strftime("%Y%m%d%H%M%S"))


def get_agent_id() -> str:
    """Get agent ID from environment."""
    return os.environ.get("HERMES_AGENT_ID", "hermes")


def log_query(
    api: str,
    entity_id: Optional[str] = None,
    kind_filter: Optional[str] = None,
    facts_requested: int = 1,
    facts_found: int = 0,
    used_kernel: bool = True,
    latency_ms: float = 0.0,
) -> None:
    """Log a query event. Called automatically by cmdb.api wrappers."""
    ensure_dirs()
    
    # Dataset snapshot: entity_count@timestamp
    try:
        from pathlib import Path
        from cmdb.engine import get_engine
        engine = get_engine(Path.home() / "knowledge" / "knowledge-kernel")
        stats = engine.get_stats()
        dataset_snapshot = f"{stats.entity_count}@{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')}"
    except Exception:
        dataset_snapshot = None
    
    event = QueryEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        session_id=get_session_id(),
        agent_id=get_agent_id(),
        api=api,
        entity_id=entity_id,
        kind_filter=kind_filter,
        facts_requested=facts_requested,
        facts_found=facts_found,
        used_kernel=used_kernel,
        latency_ms=round(latency_ms, 2),
        dataset_snapshot=dataset_snapshot,
    )
    with QUERIES_FILE.open("a") as f:
        f.write(event.to_jsonl() + "\n")


def log_assertion(assertion: str, fact_ids: List[str]) -> None:
    """Log an agent-declared assertion event."""
    ensure_dirs()
    event = AssertionEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        session_id=get_session_id(),
        agent_id=get_agent_id(),
        assertion=assertion,
        fact_ids=fact_ids,
    )
    with ASSERTIONS_FILE.open("a") as f:
        f.write(event.to_jsonl() + "\n")


# ---- Integration hooks ----------------------------------------------------

def wrap_cmdb_api():
    """
    Wrap cmdb.api functions to automatically log query events.
    Call this once at Hermes startup.
    """
    from cmdb import api as cmdb_api
    import time
    from functools import wraps

    def _log_and_call(original_fn, *args, **kwargs):
        start = time.perf_counter()
        result = original_fn(*args, **kwargs)
        latency_ms = (time.perf_counter() - start) * 1000

        # Extract metadata based on API
        api_name = original_fn.__name__
        entity_id = None
        kind_filter = None
        facts_requested = 1
        facts_found = 0

        if api_name == "cmdb_get":
            entity_id = args[0] if args else kwargs.get("entity_id")
            facts_found = 1 if getattr(result, "exists", False) else 0

        elif api_name == "cmdb_exists":
            entity_id = args[0] if args else kwargs.get("entity_id")
            facts_found = 1 if result.get("exists", False) else 0

        elif api_name == "cmdb_impact":
            entity_id = args[0] if args else kwargs.get("entity_id")
            facts_found = 1 if result.get("exists", False) else 0

        elif api_name == "cmdb_list":
            kind_filter = args[0] if args else kwargs.get("kind")
            facts_requested = 1  # One list query
            facts_found = len(result) if isinstance(result, list) else 0

        elif api_name == "cmdb_search":
            facts_requested = 1
            facts_found = len(result) if isinstance(result, list) else 0

        log_query(
            api=api_name,
            entity_id=entity_id,
            kind_filter=kind_filter,
            facts_requested=facts_requested,
            facts_found=facts_found,
            used_kernel=True,
            latency_ms=latency_ms,
        )

        return result

    # Wrap all public functions
    for fn_name in ["cmdb_get", "cmdb_exists", "cmdb_list", "cmdb_search", "cmdb_impact"]:
        if hasattr(cmdb_api, fn_name):
            original = getattr(cmdb_api, fn_name)
            setattr(cmdb_api, fn_name, lambda *args, _fn=original, **kwargs: _log_and_call(_fn, *args, **kwargs))


# ---- CLI ------------------------------------------------------------------

if __name__ == "__main__":
    # Test: log a few fake events
    ensure_dirs()
    print(f"Telemetry dir: {TELEMETRY_DIR}")
    print(f"Queries file: {QUERIES_FILE}")
    print(f"Assertions file: {ASSERTIONS_FILE}")

    # Fake event
    log_query(
        api="cmdb_get",
        entity_id="test-entity",
        facts_requested=1,
        facts_found=1,
        latency_ms=0.42,
    )
    log_assertion(
        assertion="Test entity exists",
        fact_ids=["test-entity"],
    )
    print("Logged 2 test events.")