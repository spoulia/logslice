"""Main CLI entry-point for logslice."""

from __future__ import annotations

import argparse
import sys

from logslice.cli_aggregate import add_aggregate_subparser, run_aggregate
from logslice.cli_export import add_export_subparser, run_export
from logslice.cli_highlight import add_highlight_subparser, run_highlight
from logslice.cli_redact import add_redact_subparser, run_redact
from logslice.cli_summary import add_summary_subparser, run_summary
from logslice.cli_tail import add_tail_subparser, run_tail
from logslice.core import filter_logs
from logslice.formatters import get_formatter
from logslice.output import write_entries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and analysis utility.",
    )
    parser.add_argument("--version", action="version", version="logslice 0.1.0")

    sub = parser.add_subparsers(dest="command")

    # filter (default / top-level)
    filter_p = sub.add_parser("filter", help="Filter log entries.")
    filter_p.add_argument("input", nargs="?", help="Input log file")
    filter_p.add_argument("--level", help="Minimum log level")
    filter_p.add_argument("--pattern", help="Regex pattern to match")
    filter_p.add_argument(
        "--format", choices=["plain", "json", "csv"], default="plain"
    )

    add_summary_subparser(sub)
    add_tail_subparser(sub)
    add_highlight_subparser(sub)
    add_redact_subparser(sub)
    add_aggregate_subparser(sub)
    add_export_subparser(sub)

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "filter" or args.command is None:
        source = open(args.input) if getattr(args, "input", None) else sys.stdin
        try:
            entries = filter_logs(
                source,
                min_level=getattr(args, "level", None),
                pattern=getattr(args, "pattern", None),
            )
            fmt = get_formatter(getattr(args, "format", "plain"))
            write_entries(entries, fmt)
        finally:
            if source is not sys.stdin:
                source.close()
        return 0

    dispatch = {
        "summary": run_summary,
        "tail": run_tail,
        "highlight": run_highlight,
        "redact": run_redact,
        "aggregate": run_aggregate,
        "export": run_export,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    handler(args)
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run())
