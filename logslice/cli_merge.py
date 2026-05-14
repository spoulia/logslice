"""CLI sub-command: merge – combine multiple log files in time order."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.merge import merge_files


def add_merge_subparser(subparsers) -> None:
    """Register the ``merge`` sub-command on *subparsers*."""
    p: argparse.ArgumentParser = subparsers.add_parser(
        "merge",
        help="Merge multiple log files into a single time-ordered stream.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Log files to merge (at least two recommended).",
    )
    p.add_argument(
        "--key",
        default=None,
        metavar="FIELD",
        help="Entry field to use as the sort key (default: auto-detect timestamp).",
    )
    p.add_argument(
        "--format",
        choices=["json", "plain"],
        default="json",
        dest="fmt",
        help="Output format (default: json).",
    )
    p.add_argument(
        "--out",
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout.",
    )
    p.set_defaults(func=run_merge)


def run_merge(args: argparse.Namespace) -> None:
    """Execute the merge sub-command."""
    from logslice.merge import merge_sorted  # noqa: F401 – used via merge_files

    entries = list(merge_files(args.files))

    lines: List[str] = []
    if args.fmt == "json":
        for entry in entries:
            lines.append(json.dumps(entry))
    else:
        for entry in entries:
            ts = entry.get("timestamp") or entry.get("time") or ""
            level = entry.get("level") or ""
            msg = entry.get("message") or entry.get("msg") or str(entry)
            parts = [p for p in (ts, level.upper(), msg) if p]
            lines.append(" ".join(parts))

    output = "\n".join(lines)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(output)
            if output:
                fh.write("\n")
    else:
        if output:
            print(output)
