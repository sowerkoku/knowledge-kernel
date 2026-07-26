# ---
# benchmark_lifecycle.py
# ======================
#
# PURPOSE: Measure the cost of constructing a KernelEngine from a cold state.
#
# The benchmark spawns a fresh subprocess for each measured run, so each
# measurement covers the full cost of: interpreter start, imports, filesystem
# walk, YAML parsing, index construction, hash computation, statistics.
#
# This benchmark answers one question only:
#
#   How expensive is it to bring the Engine into existence in a fresh
#   Python process?
#
# ASSUMPTIONS:
#   - kernel processes the YAMLs in cmdb.dataset.yaml (config)
#   - subprocess isolation prevents Python/runtime cache reuse
#   - filesystem cache state is not controlled (no cache priming, no flush)
#
# NOT_MEASURING:
#   - query latency        (use benchmark_queries.py)
#   - context composition  (use benchmark_context.py)
#   - memory pressure      (use benchmark_memory.py when added)
#   - steady-state hot reads
#
# USE:  python3 benchmarks/benchmark_lifecycle.py
# Writes benchmarks/lifecycle_results.json and prints summary to stdout.
# ---

import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

WORKER = """
import json, sys, time
sys.path.insert(0, {repo!r})
from cmdb.engine import get_engine
from pathlib import Path
from cmdb.config import get_config
t0 = time.perf_counter()
engine = get_engine(get_config().data_dir)
t1 = time.perf_counter()
info  = engine.get_engine_info()
print(json.dumps({{"us": (t1 - t0) * 1_000_000,
                    "entities": info["entities"],
                    "dataset_hash": info["dataset_hash"],
                    "memory_estimate_kb": info["memory_estimate_kb"],
                    "indexes": info["indexes"]}}))
"""


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

    samples_us = [r["us"] for r in runs]
    samples_us_sorted = sorted(samples_us)

    stats = {
        "n":    len(samples_us),
        "min":  samples_us_sorted[0],
        "p50":  samples_us_sorted[len(samples_us) // 2],
        "p95":  samples_us_sorted[max(0, int(0.95 * len(samples_us)) - 1)],
        "max":  samples_us_sorted[-1],
        "mean": statistics.mean(samples_us),
        "unit": "microseconds",
    }

    out = {
        "purpose":          "Engine cold-start cost",
        "samples":          samples_us,
        "stats":            stats,
        "engine_state_after": {
            "entities":           runs[0]["entities"],
            "dataset_hash":       runs[0]["dataset_hash"],
            "memory_estimate_kb": runs[0]["memory_estimate_kb"],
            "indexes":            runs[0]["indexes"],
        },
        "notes": [
            "Each sample is a fresh subprocess: no Python/runtime cache reuse.",
            "Includes: interpreter start, imports, walkdir, yaml parsing, index build, hash.",
        ],
    }

    out_path = Path(__file__).parent / "lifecycle_results.json"
    out_path.write_text(json.dumps(out, indent=2))

    print(f"Engine initialisation ({SAMPLES} fresh subprocesses):")
    print(f"  min:    {stats['min']:>10.0f} us")
    print(f"  p50:    {stats['p50']:>10.0f} us")
    print(f"  p95:    {stats['p95']:>10.0f} us")
    print(f"  max:    {stats['max']:>10.0f} us")
    print(f"  mean:   {stats['mean']:>10.0f} us")
    print()
    print(f"Dataset state after init:")
    print(f"  entities:          {runs[0]['entities']}")
    print(f"  dataset_hash:      {runs[0]['dataset_hash']}")
    print(f"  memory_kb:         {runs[0]['memory_estimate_kb']}")
    print(f"  indexes:           {runs[0]['indexes']}")
    print()
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
