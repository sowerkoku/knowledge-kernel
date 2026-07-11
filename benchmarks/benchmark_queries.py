#!/usr/bin/env python3
"""
Benchmark suite for Knowledge Kernel L2 evaluation.

Measures:
- cmdb_get(entity_id)
- cmdb_list(kind)
- cmdb_search(query)
- cmdb_impact(entity_id)
- batch queries (N sequential calls)

Reports: P50, P95, max latency, dataset size, memory estimate.
"""

import os
import sys
import time
import statistics
from pathlib import Path

# Ensure repo is importable
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Set data dir
os.environ["CMDB_DATA_DIR"] = str(Path.home() / "knowledge" / "knowledge-kernel")

from cmdb.api import cmdb_get, cmdb_list, cmdb_search, cmdb_impact


def time_ms(fn, *args, **kwargs):
    """Run fn and return (result, elapsed_ms)."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000
    return result, elapsed


def percentile(data: list[float], p: float) -> float:
    """Compute p-th percentile (0-100)."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = int(len(sorted_data) * p / 100)
    return sorted_data[min(k, len(sorted_data) - 1)]


def run_benchmark(name: str, latencies: list[float]) -> dict:
    """Format benchmark results."""
    if not latencies:
        return {"name": name, "runs": 0}
    return {
        "name": name,
        "runs": len(latencies),
        "p50_ms": round(percentile(latencies, 50), 1),
        "p95_ms": round(percentile(latencies, 95), 1),
        "p99_ms": round(percentile(latencies, 99), 1),
        "avg_ms": round(statistics.mean(latencies), 1),
        "max_ms": round(max(latencies), 1),
        "min_ms": round(min(latencies), 1),
    }


def main():
    print("=" * 70)
    print("Knowledge Kernel — L2 Benchmark (PRE-engine baseline)")
    print("=" * 70)
    print(f"Dataset: {os.environ['CMDB_DATA_DIR']}")
    print()

    results = {}

    # ---- 1. cmdb_get (existent) ----
    print("Running cmdb_get('ollama')...")
    lats = []
    for _ in range(20):
        _, ms = time_ms(cmdb_get, "ollama")
        lats.append(ms)
    results["cmdb_get_ollama"] = run_benchmark("cmdb_get(ollama)", lats)

    # ---- 2. cmdb_get (non-existent) ----
    print("Running cmdb_get('nonexistent')...")
    lats = []
    for _ in range(20):
        _, ms = time_ms(cmdb_get, "nonexistent-xyz-12345")
        lats.append(ms)
    results["cmdb_get_nonexistent"] = run_benchmark("cmdb_get(nonexistent)", lats)

    # ---- 3. cmdb_list(kind="asset") ----
    print("Running cmdb_list(kind='asset')...")
    lats = []
    for _ in range(20):
        _, ms = time_ms(cmdb_list, "asset")
        lats.append(ms)
    results["cmdb_list_asset"] = run_benchmark("cmdb_list(asset)", lats)

    # ---- 4. cmdb_list(kind="software") ----
    print("Running cmdb_list(kind='software')...")
    lats = []
    for _ in range(20):
        _, ms = time_ms(cmdb_list, "software")
        lats.append(ms)
    results["cmdb_list_software"] = run_benchmark("cmdb_list(software)", lats)

    # ---- 5. cmdb_list(kind="endpoint") ----
    print("Running cmdb_list(kind='endpoint')...")
    lats = []
    for _ in range(20):
        _, ms = time_ms(cmdb_list, "endpoint")
        lats.append(ms)
    results["cmdb_list_endpoint"] = run_benchmark("cmdb_list(endpoint)", lats)

    # ---- 6. cmdb_search ----
    print("Running cmdb_search('ollama')...")
    lats = []
    for _ in range(20):
        _, ms = time_ms(cmdb_search, "ollama")
        lats.append(ms)
    results["cmdb_search_ollama"] = run_benchmark("cmdb_search(ollama)", lats)

    # ---- 7. cmdb_impact ----
    print("Running cmdb_impact('ollama')...")
    lats = []
    for _ in range(20):
        _, ms = time_ms(cmdb_impact, "ollama")
        lats.append(ms)
    results["cmdb_impact_ollama"] = run_benchmark("cmdb_impact(ollama)", lats)

    # ---- 8. Batch sequential: 50 cmdb_get calls ----
    print("Running batch: 50x cmdb_get(ollama)...")
    lats = []
    for _ in range(50):
        _, ms = time_ms(cmdb_get, "ollama")
        lats.append(ms)
    results["batch_50x_cmdb_get"] = run_benchmark("batch 50x cmdb_get(ollama)", lats)

    # ---- 9. Batch sequential: 50 mixed calls ----
    print("Running batch: 50 mixed queries...")
    test_ids = ["ollama", "orange-pi-54", "hermes", "ollama-api", "hermes-ingenierosql"]
    lats = []
    for i in range(50):
        eid = test_ids[i % len(test_ids)]
        _, ms = time_ms(cmdb_get, eid)
        lats.append(ms)
    results["batch_50x_mixed"] = run_benchmark("batch 50x mixed cmdb_get", lats)

    # ---- Print summary ----
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    for key, r in results.items():
        print(f"\n{r['name']}:")
        print(f"  Runs:     {r['runs']}")
        print(f"  P50:      {r['p50_ms']} ms")
        print(f"  P95:      {r['p95_ms']} ms")
        print(f"  P99:      {r['p99_ms']} ms")
        print(f"  Avg:      {r['avg_ms']} ms")
        print(f"  Max:      {r['max_ms']} ms")
        print(f"  Min:      {r['min_ms']} ms")

    # Overall P95 across all
    all_p95 = [r["p95_ms"] for r in results.values() if r["runs"] > 0]
    overall_p95 = max(all_p95) if all_p95 else 0
    print(f"\n{'=' * 70}")
    print(f"OVERALL P95 (max across operations): {overall_p95} ms")
    print(f"{'=' * 70}")

    # Save to JSON for comparison
    import json
    out_file = Path(__file__).parent / "benchmark_results_pre.json"
    out_file.write_text(json.dumps(results, indent=2))
    print(f"\nSaved to: {out_file}")


if __name__ == "__main__":
    main()