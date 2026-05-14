"""CLI sub-command: enrich — attach derived fields to log entries."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from logslice.enrich import (
    apply_enrichers,
    enrich_with_hostname,
    enrich_with_regex,
    enrich_with_static,
)


def add_enrich_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("enrich", help="Attach derived fields to log entries")
    p.add_argument("file", nargs="?", help="NDJSON log file (default: stdin)")
    p.add_argument(
        "--hostname",
        action="store_true",
        default=False,
        help="Inject the local hostname as 'host'",
    )
    p.add_argument(
        "--static",
        metavar="KEY=VALUE",
        nargs="+",
        default=[],
        help="Static key=value pairs to merge into every entry",
    )
    p.add_argument(
        "--regex",
        metavar="FIELD:PATTERN",
        nargs="+",
        default=[],
        help="Extract named groups from FIELD using PATTERN",
    )


def _read_entries(path: str | None) -> List[Dict[str, Any]]:
    fh = open(path) if path else sys.stdin
    try:
        return [json.loads(line) for line in fh if line.strip()]
    finally:
        if path:
            fh.close()


def run_enrich(args: argparse.Namespace) -> None:
    entries = _read_entries(getattr(args, "file", None))
    enrichers = []

    if args.hostname:
        enrichers.append(enrich_with_hostname)

    for pair in args.static:
        if "=" not in pair:
            print(f"[enrich] invalid --static value (expected KEY=VALUE): {pair}", file=sys.stderr)
            sys.exit(1)
        k, v = pair.split("=", 1)
        enrichers.append(enrich_with_static({k: v}))

    for spec in args.regex:
        if ":" not in spec:
            print(f"[enrich] invalid --regex value (expected FIELD:PATTERN): {spec}", file=sys.stderr)
            sys.exit(1)
        field, pattern = spec.split(":", 1)
        enrichers.append(enrich_with_regex(field, pattern))

    results = apply_enrichers(entries, enrichers)
    for entry in results:
        print(json.dumps(entry))
