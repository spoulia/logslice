"""CLI sub-command: export — write filtered log entries to a file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.core import parse_log_line
from logslice.export import export_entries


def add_export_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "export",
        help="Export log entries to json, csv, or ndjson format.",
    )
    p.add_argument("input", nargs="?", help="Input log file (default: stdin)")
    p.add_argument("-o", "--output", required=True, help="Output file path")
    p.add_argument(
        "-f",
        "--format",
        choices=["json", "csv", "ndjson"],
        default="json",
        help="Output format (default: json)",
    )
    p.add_argument(
        "--fields",
        nargs="+",
        metavar="FIELD",
        help="Fields to include in CSV export (default: all)",
    )
    p.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: 2)",
    )


def _read_entries(path: str | None) -> list[dict]:
    if path:
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
    else:
        lines = sys.stdin.readlines()
    return [e for line in lines if (e := parse_log_line(line.rstrip())) is not None]


def run_export(args: argparse.Namespace) -> None:
    entries = _read_entries(getattr(args, "input", None))

    kwargs: dict = {}
    if args.format == "csv" and args.fields:
        kwargs["fields"] = args.fields
    if args.format == "json":
        kwargs["indent"] = args.indent

    content = export_entries(entries, args.format, **kwargs)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"Exported {len(entries)} entries to {out_path} ({args.format})")
