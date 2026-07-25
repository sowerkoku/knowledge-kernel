#!/usr/bin/env python3
"""
Daily Telemetry Report Generator

Generates text report from telemetry logs.

Usage:
    python3 report.py [--days N] [--output path/to/report.txt]
"""

import sys
from pathlib import Path
from .grounding_logger import QUERIES_FILE, ASSERTIONS_FILE
from .metrics import load_events, compute_metrics, format_report


def main():
    days = None
    output_path = None

    args = sys.argv[1:]
    if "--days" in args:
        idx = args.index("--days")
        if idx + 1 < len(args):
            days = int(args[idx + 1])

    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_path = Path(args[idx + 1])

    # Load events
    queries = load_events(QUERIES_FILE, days)
    assertions = load_events(ASSERTIONS_FILE, days)

    # Compute metrics
    metrics = compute_metrics(queries, assertions, days)

    # Generate report
    report = format_report(metrics)

    # Output
    if output_path:
        output_path.write_text(report)
        print(f"Report saved to: {output_path}")
    else:
        print(report)


if __name__ == "__main__":
    main()