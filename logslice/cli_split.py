"""CLI sub-command: split — divide a log stream into chunks."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.split import split_entries


def add_split_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "split",
        help="Split log entries into labelled chunks",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--count", type=int, metavar="N",
        help="Split into chunks of N entries",
    )
    group.add_argument(
        "--field", metavar="FIELD",
        help="Split whenever FIELD value changes",
    )
    group.add_argument(
        "--interval", type=float, metavar="SECONDS",
        help="Split by time window of SECONDS",
    )
    parser.add_argument(
        "--label-field", default="_chunk", metavar="KEY",
        help="Field name used to annotate chunk index (default: _chunk)",
    )
    parser.add_argument(
        "input", nargs="?", default="-",
        help="Input NDJSON file (default: stdin)",
    )


def _read_entries(path: str) -> List[dict]:
    fh = sys.stdin if path == "-" else open(path)
    try:
        return [json.loads(line) for line in fh if line.strip()]
    finally:
        if path != "-":
            fh.close()


def run_split(args: argparse.Namespace) -> None:
    entries = _read_entries(args.input)
    kwargs: dict = {}
    if args.count is not None:
        kwargs["count"] = args.count
    elif args.field is not None:
        kwargs["field"] = args.field
    else:
        kwargs["interval_seconds"] = args.interval

    label_field = args.label_field
    for chunk_index, chunk in enumerate(split_entries(entries, **kwargs)):
        for entry in chunk:
            entry[label_field] = chunk_index
            sys.stdout.write(json.dumps(entry) + "\n")
