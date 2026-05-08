"""CLI sub-command: aggregate — group and count log entries."""

import json
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from logslice.aggregate import count_by_field, count_by_time
from logslice.core import parse_log_line


def add_aggregate_subparser(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "aggregate",
        help="Group and count log entries by a field or time bucket.",
    )
    p.add_argument("input", nargs="?", default="-", help="Log file to read (default: stdin).")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--by-field", metavar="FIELD", help="Field name to aggregate by.")
    mode.add_argument(
        "--by-time",
        metavar="INTERVAL",
        choices=["minute", "hour", "day"],
        help="Time interval to bucket entries into.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=run_aggregate)


def _read_entries(path: str) -> List[dict]:
    if path == "-":
        lines = sys.stdin.readlines()
    else:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    return [e for e in (parse_log_line(line) for line in lines) if e is not None]


def run_aggregate(args: Namespace) -> None:
    entries = _read_entries(args.input)

    if args.by_field:
        counts = count_by_field(entries, args.by_field)
        label = f"field:{args.by_field}"
    else:
        counts = count_by_time(entries, args.by_time)
        label = f"time:{args.by_time}"

    if args.format == "json":
        print(json.dumps({"aggregation": label, "counts": counts}, indent=2))
    else:
        print(f"Aggregation by {label}")
        print("-" * 40)
        for key, count in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"  {key:<30} {count}")
        print("-" * 40)
        print(f"  {'TOTAL':<30} {sum(counts.values())}")
