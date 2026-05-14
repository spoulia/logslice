"""CLI sub-command: label — tag log entries by pattern or field value."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from logslice.label import filter_by_label, label_by_field, label_by_pattern


def add_label_subparser(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "label",
        help="Attach labels to log entries and optionally filter by label.",
    )
    p.add_argument("input", nargs="?", default="-", help="Input file (default: stdin)")
    p.add_argument(
        "--pattern",
        metavar="REGEX",
        help="Regex pattern to match against --field.",
    )
    p.add_argument(
        "--field",
        default="message",
        help="Entry field to match pattern against (default: message).",
    )
    p.add_argument(
        "--label",
        default="tagged",
        help="Label string to attach when pattern matches (default: tagged).",
    )
    p.add_argument(
        "--map",
        metavar="FIELD=VALUE:LABEL",
        action="append",
        dest="mappings",
        default=[],
        help="Field=value:label mapping, may be repeated.",
    )
    p.add_argument(
        "--filter",
        metavar="LABEL",
        dest="filter_label",
        help="Only output entries that carry this label.",
    )
    p.add_argument(
        "--label-key",
        default="label",
        help="Key used to store labels on entries (default: label).",
    )


def _read_entries(source: str) -> List[dict]:
    fh = sys.stdin if source == "-" else open(source)
    entries = []
    try:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    entries.append({"message": line})
    finally:
        if fh is not sys.stdin:
            fh.close()
    return entries


def run_label(args: Namespace) -> None:
    entries = _read_entries(args.input)

    if args.pattern:
        entries = label_by_pattern(
            entries,
            pattern=args.pattern,
            label=args.label,
            field=args.field,
            label_key=args.label_key,
        )

    if args.mappings:
        mapping = {}
        for m in args.mappings:
            if ":" in m:
                kv, lbl = m.rsplit(":", 1)
                mapping[kv] = lbl
        if mapping:
            entries = label_by_field(entries, mapping, label_key=args.label_key)

    if args.filter_label:
        entries = filter_by_label(entries, args.filter_label, label_key=args.label_key)

    for entry in entries:
        print(json.dumps(entry))
