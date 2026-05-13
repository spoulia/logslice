"""CLI sub-command: validate log entries against a schema."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.schema import SchemaError, available_schemas, filter_valid, load_schema, validate_entry


def add_schema_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "schema",
        help="Validate structured log entries against a field schema.",
    )
    p.add_argument("input", nargs="?", default="-", help="NDJSON input file (default: stdin)")
    p.add_argument(
        "--schema",
        default="basic",
        help=f"Schema preset or JSON object. Built-ins: {available_schemas()}",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Reject entries with fields not defined in the schema.",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="Print violations instead of filtering them out.",
    )
    p.set_defaults(func=run_schema)


def _read_entries(path: str) -> List[dict]:
    fh = sys.stdin if path == "-" else open(path)
    try:
        return [json.loads(line) for line in fh if line.strip()]
    finally:
        if path != "-":
            fh.close()


def run_schema(args: argparse.Namespace) -> int:
    # Resolve schema
    raw = args.schema
    try:
        if raw.startswith("{"):
            schema = {k: __builtins__[v] if isinstance(__builtins__, dict) else getattr(__builtins__, v, str)  # type: ignore[index]
                      for k, v in json.loads(raw).items()}
        else:
            schema = load_schema(raw)
    except KeyError:
        print(f"error: unknown schema preset '{raw}'", file=sys.stderr)
        return 1

    entries = _read_entries(args.input)

    if args.report:
        found_any = False
        for i, entry in enumerate(entries):
            violations = validate_entry(entry, schema, strict=args.strict)
            if violations:
                found_any = True
                print(f"entry {i}: " + "; ".join(violations))
        return 1 if found_any else 0

    valid = filter_valid(entries, schema, strict=args.strict)
    for entry in valid:
        print(json.dumps(entry))
    return 0
