"""CLI sub-command: normalize — apply field normalizers to log entries."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.normalize import normalize_entries


def add_normalize_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *normalize* sub-command."""
    p = subparsers.add_parser(
        "normalize",
        help="Apply field normalizers to NDJSON log entries read from stdin.",
    )
    p.add_argument(
        "--field",
        metavar="FIELD:NORM",
        action="append",
        dest="fields",
        default=[],
        help=(
            "Field and normalizer in FIELD:NORM format. "
            "May be repeated. Supported: lower, upper, strip, int, float, bool, str."
        ),
    )
    p.add_argument(
        "--level",
        action="store_true",
        default=False,
        help="Shortcut: uppercase the 'level' field.",
    )
    p.set_defaults(func=run_normalize)


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


def run_normalize(args: argparse.Namespace, stream=None, out=None) -> None:
    """Execute the normalize sub-command."""
    out = out or sys.stdout

    spec: dict = {}
    for pair in args.fields:
        if ":" not in pair:
            print(f"Invalid --field value {pair!r}: expected FIELD:NORM", file=sys.stderr)
            sys.exit(1)
        field, norm = pair.split(":", 1)
        spec[field.strip()] = norm.strip()

    if args.level:
        spec.setdefault("level", "upper")

    entries = _read_entries(stream)

    try:
        result = normalize_entries(entries, spec)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    for entry in result:
        out.write(json.dumps(entry) + "\n")
