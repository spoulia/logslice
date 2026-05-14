"""CLI sub-command: partition — split log entries into labelled buckets."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.partition import (
    partition_by_field,
    partition_by_pattern,
    partition_sizes,
)


def add_partition_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "partition",
        help="Split log entries into named buckets.",
    )
    p.add_argument(
        "--field",
        default="level",
        help="Entry field to partition by (default: level).",
    )
    p.add_argument(
        "--pattern",
        dest="patterns",
        metavar="LABEL=REGEX",
        action="append",
        default=[],
        help="Pattern rule as LABEL=REGEX; may be repeated.",
    )
    p.add_argument(
        "--sizes-only",
        action="store_true",
        default=False,
        help="Print bucket sizes instead of full entries.",
    )
    p.add_argument(
        "input",
        nargs="?",
        default="-",
        help="NDJSON input file (default: stdin).",
    )
    p.set_defaults(func=run_partition)


def _read_entries(path: str) -> List[dict]:
    fh = sys.stdin if path == "-" else open(path)
    try:
        return [json.loads(line) for line in fh if line.strip()]
    finally:
        if path != "-":
            fh.close()


def run_partition(args: argparse.Namespace) -> None:
    entries = _read_entries(args.input)

    if args.patterns:
        pairs = []
        for raw in args.patterns:
            if "=" not in raw:
                print(f"Invalid pattern spec (expected LABEL=REGEX): {raw}", file=sys.stderr)
                sys.exit(1)
            label, _, regex = raw.partition("=")
            pairs.append((label.strip(), regex.strip()))
        pm = partition_by_pattern(entries, pairs, field=args.field)
    else:
        pm = partition_by_field(entries, args.field)

    if args.sizes_only:
        print(json.dumps(partition_sizes(pm), indent=2))
        return

    output = {key: list(bucket) for key, bucket in pm.items()}
    print(json.dumps(output, indent=2))
