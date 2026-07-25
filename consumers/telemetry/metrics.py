"""
Telemetry Metrics Calculator

Computes KAR, FGR, Fact Miss Rate, Fact Coverage, Availability, Query Distribution
from append-only JSONL event logs.

Usage:
    python3 metrics.py [--days N] [--output report.txt]
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any, Optional

from .grounding_logger import QUERIES_FILE, ASSERTIONS_FILE, QueryEvent, AssertionEvent


def load_events(file: Path, days: Optional[int] = None) -> List[dict]:
    """Load JSONL events, optionally filtered by recency."""
    if not file.exists():
        return []

    events = []
    cutoff = None
    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    with file.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            ts = datetime.fromisoformat(event["timestamp"])
            if cutoff and ts < cutoff:
                continue
            events.append(event)

    return events


def compute_metrics(queries: List[dict], assertions: List[dict], days: Optional[int] = None) -> dict:
    """
    Compute all telemetry metrics.

    Returns:
    {
        "period": {"days": int, "start": str, "end": str},
        "queries": {...},
        "assertions": {...},
        "kar": float,
        "fgr": float,
        "fact_miss_rate": float,
        "fact_coverage": float,
        "availability": float,
        "api_distribution": {...},
        "latency": {"p50": float, "p95": float, "avg": float},
    }
    """
    if not queries:
        return {"error": "No queries found"}

    # Time window
    timestamps = [datetime.fromisoformat(e["timestamp"]) for e in queries]
    start_ts = min(timestamps)
    end_ts = max(timestamps)
    days_span = (end_ts - start_ts).total_seconds() / 86400

    # ---- Query-level metrics ----
    total_queries = len(queries)
    queries_using_kernel = sum(1 for q in queries if q.get("used_kernel", False))
    queries_needing_facts = total_queries  # All queries need facts by definition

    # KAR: Kernel Adoption Rate
    kar = queries_using_kernel / queries_needing_facts if queries_needing_facts > 0 else 0.0

    # Fact Coverage (per-query average)
    # For cmdb_get/cmdb_exists/cmdb_impact: facts_requested=1, facts_found∈{0,1}
    # For cmdb_list/cmdb_search: facts_requested=1, facts_found=N (count)
    # Coverage = min(1, found/requested) to avoid >100%
    coverages = []
    for q in queries:
        req = q.get("facts_requested", 1)
        found = q.get("facts_found", 0)
        cov = min(1.0, found / req) if req > 0 else 0.0
        coverages.append(cov)
    fact_coverage = sum(coverages) / len(coverages) if coverages else 0.0

    # Fact Miss Rate: queries that found ZERO facts when they needed some
    queries_with_no_results = sum(1 for q in queries if q.get("facts_found", 0) == 0 and q.get("used_kernel", False))
    fact_miss_rate = queries_with_no_results / queries_using_kernel if queries_using_kernel > 0 else 0.0

    # Availability (queries with ALL facts found)
    # For single-entity queries: found >= requested means success
    queries_with_all_facts = sum(1 for q in queries if q.get("facts_found", 0) >= q.get("facts_requested", 1))
    availability = queries_with_all_facts / queries_using_kernel if queries_using_kernel > 0 else 0.0

    # API Distribution
    api_counts = defaultdict(int)
    for q in queries:
        api_counts[q.get("api", "unknown")] += 1
    api_distribution = {
        api: {"count": count, "pct": round(count / total_queries * 100, 1)}
        for api, count in sorted(api_counts.items(), key=lambda x: -x[1])
    }

    # Latency
    latencies = [q.get("latency_ms", 0) for q in queries if q.get("latency_ms", 0) > 0]
    if latencies:
        sorted_lats = sorted(latencies)
        p50 = sorted_lats[int(len(sorted_lats) * 0.50)]
        p95 = sorted_lats[int(len(sorted_lats) * 0.95)]
        avg = sum(latencies) / len(latencies)
    else:
        p50 = p95 = avg = 0.0

    # ---- Assertion-level metrics (FGR) ----
    total_assertions = len(assertions)
    grounded_assertions = sum(1 for a in assertions if a.get("fact_ids"))
    fgr = grounded_assertions / total_assertions if total_assertions > 0 else 0.0

    return {
        "period": {
            "days": round(days_span, 1),
            "start": start_ts.isoformat(),
            "end": end_ts.isoformat(),
        },
        "queries": {
            "total": total_queries,
            "using_kernel": queries_using_kernel,
        },
        "assertions": {
            "total": total_assertions,
            "grounded": grounded_assertions,
        },
        "kar": round(kar * 100, 1),  # percentage
        "fgr": round(fgr * 100, 1),  # percentage
        "fact_miss_rate": round(fact_miss_rate * 100, 1),  # percentage
        "fact_coverage": round(fact_coverage * 100, 1),  # percentage
        "availability": round(availability * 100, 1),  # percentage
        "api_distribution": api_distribution,
        "latency": {
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "avg_ms": round(avg, 2),
        },
    }


def format_report(metrics: dict) -> str:
    """Generate human-readable text report."""
    if "error" in metrics:
        return f"Error: {metrics['error']}\n"

    lines = [
        "=" * 60,
        "Knowledge Kernel — Production Telemetry Report",
        "=" * 60,
        "",
        f"Period: {metrics['period']['days']} days",
        f"  Start: {metrics['period']['start']}",
        f"  End:   {metrics['period']['end']}",
        "",
        "QUERIES",
        f"  Total:        {metrics['queries']['total']}",
        f"  Using kernel: {metrics['queries']['using_kernel']}",
        "",
        "ASSERTIONS",
        f"  Total:           {metrics['assertions']['total']}",
        f"  Grounded:        {metrics['assertions']['grounded']}",
        "",
        "KEY METRICS",
        f"  KAR (Kernel Adoption Rate):     {metrics['kar']:.1f}%",
        f"  FGR (Fact Grounding Rate):      {metrics['fgr']:.1f}%",
        f"  Fact Miss Rate:                 {metrics['fact_miss_rate']:.1f}%",
        f"  Fact Coverage:                  {metrics['fact_coverage']:.1f}%",
        f"  Availability:                   {metrics['availability']:.1f}%",
        "",
        "LATENCY",
        f"  P50: {metrics['latency']['p50_ms']:.2f} ms",
        f"  P95: {metrics['latency']['p95_ms']:.2f} ms",
        f"  Avg: {metrics['latency']['avg_ms']:.2f} ms",
        "",
        "API DISTRIBUTION",
    ]

    for api, data in metrics["api_distribution"].items():
        lines.append(f"  {api:15s} {data['count']:4d} ({data['pct']:.1f}%)")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


# ---- CLI ------------------------------------------------------------------

if __name__ == "__main__":
    days = None
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

    queries = load_events(QUERIES_FILE, days)
    assertions = load_events(ASSERTIONS_FILE, days)
    metrics = compute_metrics(queries, assertions, days)
    report = format_report(metrics)
    print(report)