# ---
# benchmark_queries.py
# ====================
#
# PURPOSE: Measure query latency of the KernelEngine once it is hot.
#
# Before timing anything, the Engine is force-loaded via get_engine(...).
# After that initial load, queries are timed in batches. Initialisation
# cost is NOT included.
#
# This benchmark answers one question only:
#
#   How fast do reads look, on an Engine that is already in memory?
#
# ASSUMPTIONS:
#   - Engine has been constructed at least once (warm state)
#   - filesystem cache is whatever the OS provides; not primed/flushed
#   - runs only one Python process
#
# NOT_MEASURING:
#   - Engine initialisation       (use benchmark_lifecycle.py)
#   - context composition         (use benchmark_context.py)
#   - memory pressure             (use benchmark_memory.py when added)
#   - dataset integrity (run cmdb_validate for that)
#
# USE:  python3 benchmarks/benchmark_queries.py
# Writes benchmarks/queries_results.json and prints summary to stdout.
# ---

import gc
import json
import random
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from cmdb.api import (
    cmdb_list, cmdb_exists, cmdb_get, cmdb_search, cmdb_impact,
)


def percentile(sorted_values, p):
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = k - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


def time_call(fn, arg):
    t0 = time.perf_counter_ns()
    fn(arg)
    t1 = time.perf_counter_ns()
    return (t1 - t0) / 1_000.0  # microseconds


def summarise(samples):
    s = sorted(samples)
    return {
        "n":    len(s),
        "min":  s[0],
        "p50":  percentile(s, 50),
        "p95":  percentile(s, 95),
        "p99":  percentile(s, 99),
        "max":  s[-1],
        "mean": statistics.mean(s),
        "stdev": statistics.stdev(s) if len(s) > 1 else 0.0,
        "unit": "microseconds",
    }


# Operations timed by entity_id (single argument).
OPERATIONS = {
    "exists": cmdb_exists,
    "get":    cmdb_get,
    "impact": cmdb_impact,
}


def main():
    random.seed(20260725)

    # Force Engine hot
    from cmdb.engine import get_engine
    from cmdb.config import get_config
    get_engine(get_config().data_dir)

    all_ids = sorted(e["id"] for e in cmdb_list())
    n_total = len(all_ids)
    print(f"Hot Engine. Dataset: {n_total} entities", file=sys.stderr)

    N_WARM   = 1000
    N_SEARCH = 200
    queries = ["ollama", "postgres", "metabase", "docker", "redis", "vault", "monitoring"]
    results = {}

    for op, fn in OPERATIONS.items():
        warm = [time_call(fn, all_ids[i % n_total]) for i in range(N_WARM)]
        rnd  = [time_call(fn, random.choice(all_ids)) for _ in range(N_WARM)]
        h_eid = all_ids[n_total // 2]
        hot  = [time_call(fn, h_eid) for _ in range(N_WARM)]
        results[op] = {
            "warm":   summarise(warm),
            "random": summarise(rnd),
            "hot":    summarise(hot),
        }

    # search() takes a query string, not an id — separate timings.
    search_samples = []
    for _ in range(N_SEARCH):
        gc.collect()
        q = random.choice(queries)
        search_samples.append(time_call(cmdb_search, q))
    results["search"] = {"warm": summarise(search_samples)}

    out = {
        "purpose":  "Engine query latency (hot state)",
        "samples":  {
            op: {m: r["n"] for m, r in mvals.items()}
            for op, mvals in results.items()
        },
        "results":  results,
        "entity_count": n_total,
        "notes": [
            "Engine preloaded via get_engine() before any timing.",
            "hot = same id; random = shuffled ids; warm = cycling ids.",
        ],
    }

    out_path = Path(__file__).parent / "queries_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))

    print("\n=== Hot query latency (microseconds) ===\n", file=sys.stderr)
    print(f"{'op':<10} {'mode':<8} {'n':<5} {'p50':<8} {'p95':<8} "
          f"{'p99':<8} {'max':<8} {'mean':<8}", file=sys.stderr)
    for op, modes in results.items():
        for mode, r in modes.items():
            print(f"{op:<10} {mode:<8} {r['n']:<5} "
                  f"{r['p50']:<8.1f} {r['p95']:<8.1f} {r['p99']:<8.1f} "
                  f"{r['max']:<8.1f} {r['mean']:<8.1f}",
                  file=sys.stderr)
    print(f"\nSaved to: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
