# ---
# benchmark_lifecycle.py
# ======================
#
# PURPOSE: Measure the cost of constructing a KernelEngine from a cold state.
#
# The benchmark spawns a fresh subprocess for each measured run. Each
# subprocess:
#   1. Imports the cmdb package
#   2. Calls KernelEngine.get_instance(...) which forces __init__
#   3. Calls reload() explicitly to guarantee that the YAML scan,
#      indexing, and hash recomputation actually run
#   4. Calls get_engine_info() to read stats after load
#
# This benchmark answers one question only:
#
#   How long does it take to bring up the Engine from scratch in a
#   process that does not have any preexisting state?
#
# ASSUMPTIONS:
#   - subprocess isolation prevents Python/state reuse
#   - filesystem cache state is not controlled (no priming, no flush)
#   - the dataset path matches the configured entities_dir
#
# NOT_MEASURING:
#   - query latency        (use benchmark_queries.py)
#   - context composition  (use benchmark_context.py)
#   - memory pressure      (use benchmark_memory.py when added)
#   - in-process reload cost only (benchmark_inprocess_reload.py would, if added)
#
# USE:  python3 benchmarks/benchmark_lifecycle.py
# Writes benchmarks/lifecycle_results.json and prints summary to stdout.
# ---

import json
import statistics
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# Worker: each phase fully timed INSIDE the cold process.
WORKER = """
import json, sys, time
sys.path.insert(0, {repo!r})

# Whole-process startup (no engine yet).
t0 = time.perf_counter()
from cmdb.engine import get_engine, clear_engine_cache
from cmdb.config import get_config
e_dir = get_config().data_dir
t_import = (time.perf_counter() - t0) * 1_000_000

# First-time construction: creates a KernelEngine and triggers reload()
# because get_engine_info() forces ensure_loaded().
clear_engine_cache(e_dir)
t1 = time.perf_counter()
engine = get_engine(e_dir)
t_get = (time.perf_counter() - t1) * 1_000_000  # ~us — usually near 0

t2 = time.perf_counter()
info_first = engine.get_engine_info()
t_first_info = (time.perf_counter() - t2) * 1_000_000

# Explicit reload — guarantees that the YAML scan, index build, and hash
# recomputation actually run.
t3 = time.perf_counter()
engine.reload()
info_reload = engine.get_engine_info()
t_reload = (time.perf_counter() - t3) * 1_000_000

print(json.dumps({{
    "us_import_in_subprocess": t_import,
    "us_get_engine_after_init": t_get,
    "us_first_get_engine_info": t_first_info,
    "us_reload_then_info": t_reload,
    "entities": info_reload["entities"],
    "dataset_hash": info_reload["dataset_hash"],
    "memory_kb": info_reload["memory_estimate_kb"],
    "indexes": info_reload["indexes"],
}}))
"""


def percentile(sorted_values, p):
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = k - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


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
        "unit": "microseconds",
    }


def main():
    SAMPLES = 7
    runs = []
    for _ in range(SAMPLES):
        proc = subprocess.run(
            [sys.executable, "-c", WORKER.format(repo=str(REPO))],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            raise RuntimeError(f"Worker failed: returncode={proc.returncode}")
        runs.append(json.loads(proc.stdout.strip()))

    out = {
        "purpose": "KernelEngine lifecycle cost (cold subprocess)",
        "n_samples_per_subprocess": SAMPLES,
        "phases": {
            "us_import_in_subprocess":
                summarise([r["us_import_in_subprocess"] for r in runs]),
            "us_first_get_engine_info":
                summarise([r["us_first_get_engine_info"] for r in runs]),
            "us_reload_then_info":
                summarise([r["us_reload_then_info"] for r in runs]),
        },
        "engine_state_after": {
            "entities":     runs[0]["entities"],
            "dataset_hash": runs[0]["dataset_hash"],
            "memory_kb":    runs[0]["memory_kb"],
            "indexes":      runs[0]["indexes"],
        },
        "observations": [
            "us_first_get_engine_info exposes the dominant cost — it triggers",
            "  ensure_loaded(), which triggers reload() (YAML scan + index build).",
            "us_reload_then_info re-validates the same cost on a hot engine.",
            "If both figures are close to 800 ms, reload() runs every time and",
            "  in-memory indexing does not short-circuit filesystem reads.",
        ],
    }

    out_path = Path(__file__).parent / "lifecycle_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))

    print(f"Engine lifecycle ({SAMPLES} fresh subprocesses)")
    print(f"  Dataset:  {runs[0]['entities']} entities, "
          f"hash={runs[0]['dataset_hash']}, "
          f"mem~{runs[0]['memory_kb']} KB")
    print()
    for phase, stats in out["phases"].items():
        print(f"  {phase}:")
        print(f"    min:  {stats['min']:>10.0f} us")
        print(f"    p50:  {stats['p50']:>10.0f} us")
        print(f"    p95:  {stats['p95']:>10.0f} us")
        print(f"    max:  {stats['max']:>10.0f} us")
    print()
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
