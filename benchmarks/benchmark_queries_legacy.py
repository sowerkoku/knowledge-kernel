# ---
# benchmark_queries_legacy.py
# ============================
#
# Status: HISTORICAL REFERENCE — kept unmodified.
#
# This file preserves the pre-redesign benchmark structure: it mixed
# initialisation cost with hot query latency in the same %-tile, which
# produced the bimodal distribution that inadvertently surfaced the
# uncompleted canonical-representation transition in cmdb_context
# (see consumers/inspector/NOTES.md).
#
# Source JSON output preserved at benchmarks/benchmark_results_pre.json.
#
# Replaced as canonical benchmark by:
#   - benchmark_lifecycle.py  (cold start, fresh subprocess per sample)
#   - benchmark_queries.py    (queries on a preloaded Engine)
#   - benchmark_context.py    (cmdb_context composite cost)
#
# Do not run this to produce baselines; run the three above instead.
# ---
