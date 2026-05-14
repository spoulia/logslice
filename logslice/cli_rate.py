"""CLI sub-command: rate — measure or throttle log entry throughput."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.core import LogEntry, parse_log_line
from logslice.rate import measure_rate, throttle_entries, rate_summary


def add_rate_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "rate",
        help="Measure or throttle log entry throughput.",
    )
    p.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--measure",
        action="store_true",
        default=True,
        help="Annotate each entry with its rolling rate (default).",
    )
    mode.add_argument(
        "--throttle",
        metavar="MAX_RATE",
        type=float,
        default=None,
        help="Drop entries exceeding MAX_RATE entries/second.",
    )
    p.add_argument(
        "--window",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Rolling window in seconds for rate measurement (default: 60).",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a JSON throughput summary instead of entries.",
    )
    p.set_defaults(func=run_rate)


def _read_entries(path: str) -> List[LogEntry]:
    if path == "-":
        lines = sys.stdin
    else:
        lines = open(path)
    entries = [parse_log_line(line) for line in lines if line.strip()]
    if path != "-":
        lines.close()  # type: ignore[union-attr]
    return entries


def run_rate(args: argparse.Namespace) -> None:
    entries = _read_entries(args.input)

    if args.summary:
        info = rate_summary(entries)
        print(json.dumps(info))
        return

    if args.throttle is not None:
        for entry in throttle_entries(entries, max_rate=args.throttle):
            print(json.dumps(entry))
    else:
        for entry, current_rate in measure_rate(entries, window_seconds=args.window):
            entry = dict(entry)
            entry["_rate"] = round(current_rate, 4)
            print(json.dumps(entry))
