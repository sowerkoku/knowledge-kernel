#!/usr/bin/env python3
"""CLI entry point for the Knowledge Inspector.

Usage:
    PYTHONPATH=consumers/inspector python3 -m inspector.cli \\
        --stale-after-days 90 --output /tmp/inspector_report.json

Reads entities from the Knowledge Kernel via cmdb_list, runs each
registered rule (currently only stale_entity), and emits a deterministic
JSON report.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from inspector.kernel_api import default_api
from inspector.report import run_inspector
from inspector.rules.stale_entity import RULE as STALE_ENTITY_RULE


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Knowledge Inspector CLI")
    parser.add_argument("--stale-after-days", type=int, default=90)
    parser.add_argument("--output", type=str, default=None,
                        help="Write report to this file instead of stdout.")
    args = parser.parse_args(argv)

    api = default_api()
    report = run_inspector(
        rules=[STALE_ENTITY_RULE],
        api=api,
        policy={"stale_after_days": args.stale_after_days},
    )

    rendered = report.to_json()
    if args.output:
        with open(args.output, "w") as fh:
            fh.write(rendered)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
