# ---
# benchmark_context.py
# ====================
#
# PURPOSE: Measure the cost of building an agent context via cmdb_context.
#
# This is a composite operation: it composes identity, known_environment,
# dependents, warnings, etc. It is NOT a single lookup.
#
# Before timing, the Engine is force-loaded so that the part of cmdb_context
# that uses Engine is hot. The remaining cost is dominated by load_entities
# (if it is currently invoked — see NOTES.md for the in-flight transition).
#
# This benchmark exists to give a baseline that future changes can be
# compared against. Run it before any refactor that affects cmdb_context.
#
# ASSUMPTIONS:
#   - Engine is already hot
#   - filesystem cache is whatever the OS provides
#   - dataset has at least one agent entity
#
# NOT_MEASURING:
#   - Engine initialisation   (use benchmark_lifecycle.py)
#   - query latency           (use benchmark_queries.py)
#   - context correctness     (use tests/test_cmdb_context.py if it exists)
#   - memory pressure         (use benchmark_memory.py when added)
#
# USE:  python3 benchmarks/benchmark_context.py
# Writes benchmarks/context_results.json and prints summary to stdout.
# ---

import gc
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from cmdb.api import cmdb_context, cmdb_list
from cmdb.engine import get_engine
from cmdb.config import get_config


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


def main():
    # Force Engine hot
    get_engine(get_config().data_dir)

    # Find at least one agent and one non-agent for both branches.
    all_entities = cmdb_list()
    by_kind = {}
    for e in all_entities:
        by_kind.setdefault(e.get("kind"), []).append(e["id"])

    if "agent" not in by_kind or not by_kind["agent"]:
        print("No agent-kind entities found in dataset; cannot benchmark.", file=sys.stderr)
        sys.exit(2)

    agent_id = by_kind["agent"][0]
    unknown = "definitely-not-a-real-agent-xyz"

    N = 30  # small N because each call is heavier than a single lookup

    warm = []
    for _ in range(N):
        gc.collect()
        warm.append(time_call(cmdb_context, agent_id))

    miss = []
    for _ in range(N):
        gc.collect()
        miss.append(time_call(cmdb_context, unknown))

    out = {
        "purpose":   "cmdb_context composite cost",
        "entity_count": len(all_entities),
        "agent_under_test": agent_id,
        "results": {
            "known_agent":  summarise(warm),
            "unknown_agent": summarise(miss),
        },
        "notes": [
            "Each call is preceded by gc.collect() so the heap pressure of one "
            "call doesn't pre-warm the next.",
            "Until the canonical-representation transition completes (see "
            "consumers/inspector/NOTES.md), each cmdb_context call also parses "
            "all YAML files via load_entities_with_paths — that cost is included.",
        ],
    }

    out_path = Path(__file__).parent / "context_results.json"
    out_path.write_text(json.dumps(out, indent=2))

    print(f"cmdb_context composite (n={N} per branch):")
    print()
    print(f"  known_agent   ({agent_id}):")
    print(f"    min:   {out['results']['known_agent']['min']:>10.0f} us")
    print(f"    p50:   {out['results']['known_agent']['p50']:>10.0f} us")
    print(f"    p95:   {out['results']['known_agent']['p95']:>10.0f} us")
    print(f"    p99:   {out['results']['known_agent']['p99']:>10.0f} us")
    print(f"    max:   {out['results']['known_agent']['max']:>10.0f} us")
    print()
    print(f"  unknown_agent ({unknown}):")
    print(f"    min:   {out['results']['unknown_agent']['min']:>10.0f} us")
    print(f"    p50:   {out['results']['unknown_agent']['p50']:>10.0f} us")
    print(f"    p95:   {out['results']['unknown_agent']['p95']:>10.0f} us")
    print(f"    p99:   {out['results']['unknown_agent']['p99']:>10.0f} us")
    print(f"    max:   {out['results']['unknown_agent']['max']:>10.0f} us")
    print()
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
