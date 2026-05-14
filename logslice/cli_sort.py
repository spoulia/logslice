"""CLI sub-command: sort — sort log entries by a field."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.sort import sort_entries, stable_sort_entries


def add_sort_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``sort`` sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "sort",
        help="Sort log entries by one or more fields.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        metavar="FILE",
        help="NDJSON input file (default: stdin).",
    )
    parser.add_argument(
        "--field",
        "-f",
        default="timestamp",
        help="Primary field to sort by (default: timestamp).",
    )
    parser.add_argument(
        "--extra-fields",
        nargs="*",
        metavar="FIELD",
        default=[],
        help="Additional fields for a multi-key stable sort.",
    )
    parser.add_argument(
        "--reverse",
        "-r",
        action="store_true",
        default=False,
        help="Sort in descending order.",
    )
    parser.add_argument(
        "--missing-last",
        action="store_true",
        default=True,
        dest="missing_last",
        help="Place entries with missing sort field at the end (default).",
    )
    parser.set_defaults(func=run_sort)


def _read_entries(path: str) -> List[dict]:
    fh = sys.stdin if path == "-" else open(path)
    try:
        return [json.loads(line) for line in fh if line.strip()]
    finally:
        if path != "-":
            fh.close()


def run_sort(args: argparse.Namespace) -> None:
    """Execute the ``sort`` sub-command."""
    entries = _read_entries(args.input)

    if args.extra_fields:
        fields = [args.field] + list(args.extra_fields)
        result = stable_sort_entries(entries, fields=fields, reverse=args.reverse)
    else:
        result = sort_entries(
            entries,
            field=args.field,
            reverse=args.reverse,
            missing_last=args.missing_last,
        )

    for entry in result:
        sys.stdout.write(json.dumps(entry) + "\n")
