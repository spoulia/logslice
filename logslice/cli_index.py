"""CLI sub-command: index — build an in-memory index and query it."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.index import build_index


def add_index_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "index",
        help="Build an in-memory index over log entries and query by field value.",
    )
    p.add_argument(
        "--field",
        dest="fields",
        metavar="FIELD",
        action="append",
        default=None,
        help="Field(s) to index (repeatable, default: level source).",
    )
    p.add_argument(
        "--query",
        metavar="FIELD=VALUE",
        action="append",
        dest="queries",
        default=[],
        help="Query expression (repeatable). E.g. --query level=error",
    )
    p.add_argument(
        "--list-values",
        metavar="FIELD",
        dest="list_values",
        default=None,
        help="Print all distinct indexed values for FIELD and exit.",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Print index statistics instead of entries.",
    )


def _parse_query(expr: str):
    """Split 'field=value' into (field, value)."""
    if "=" not in expr:
        raise argparse.ArgumentTypeError(f"Invalid query expression: {expr!r}")
    field, _, value = expr.partition("=")
    return field.strip(), value.strip()


def _read_entries(stream=None) -> List[dict]:
    src = stream or sys.stdin
    entries = []
    for line in src:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                entries.append({"message": line})
    return entries


def run_index(args: argparse.Namespace, stream=None) -> None:
    entries = _read_entries(stream)
    idx = build_index(entries, fields=args.fields)

    if args.stats:
        fields = args.fields or ["level", "source"]
        print(f"total entries : {len(idx)}")
        for f in fields:
            vals = idx.all_values(f)
            print(f"  {f}: {len(vals)} distinct value(s)")
        return

    if args.list_values:
        for v in idx.all_values(args.list_values):
            print(v)
        return

    if not args.queries:
        for entry in idx:
            print(json.dumps(entry))
        return

    seen: set = set()
    for expr in args.queries:
        field, value = _parse_query(expr)
        for entry in idx.lookup(field, value):
            eid = id(entry)
            if eid not in seen:
                seen.add(eid)
                print(json.dumps(entry))
