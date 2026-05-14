"""CLI subcommand: diff – compare two log files and report differences."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.core import parse_log_line
from logslice.diff import diff_entries, format_diff_text


def add_diff_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("diff", help="Compare two log files")
    p.add_argument("left", help="Baseline log file")
    p.add_argument("right", help="Comparison log file")
    p.add_argument(
        "--fields",
        nargs="+",
        default=["message", "level"],
        metavar="FIELD",
        help="Fields used to identify unique entries (default: message level)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--show",
        choices=["all", "added", "removed", "common"],
        default="all",
        help="Which entries to show (default: all)",
    )


def _read_entries(path: str) -> List[dict]:
    entries = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line:
                entries.append(parse_log_line(line))
    return entries


def run_diff(args: argparse.Namespace) -> None:
    left = _read_entries(args.left)
    right = _read_entries(args.right)

    result = diff_entries(left, right, fields=args.fields)

    if args.show != "all":
        display = {args.show: result[args.show]}
    else:
        display = result

    if args.fmt == "json":
        out = {
            k: v for k, v in display.items()
        }
        json.dump(out, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
    else:
        print(format_diff_text(display))
