"""CLI sub-command: logslice tail — follow a log file in real time."""

import argparse
import sys

from logslice.tail import tail_file
from logslice.formatters import get_formatter


def add_tail_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *tail* sub-command onto *subparsers*."""
    parser = subparsers.add_parser(
        "tail",
        help="Follow a log file and print new entries as they arrive.",
    )
    parser.add_argument("file", help="Log file to follow.")
    parser.add_argument(
        "--format",
        choices=["plain", "json", "csv"],
        default="plain",
        dest="fmt",
        help="Output format (default: plain).",
    )
    parser.add_argument(
        "--level",
        default=None,
        metavar="LEVEL",
        help="Minimum log level to display (debug/info/warning/error/critical).",
    )
    parser.add_argument(
        "--pattern",
        default=None,
        metavar="PATTERN",
        help="Only show lines containing PATTERN (case-insensitive).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.25,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 0.25).",
    )
    parser.set_defaults(func=run_tail)


def run_tail(args: argparse.Namespace) -> None:
    """Entry point for the *tail* sub-command."""
    formatter = get_formatter(args.fmt)

    def _print_entry(entry: dict) -> None:
        line = formatter(entry)
        print(line, flush=True)

    try:
        tail_file(
            filepath=args.file,
            callback=_print_entry,
            poll_interval=args.interval,
            min_level=args.level,
            pattern=args.pattern,
        )
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
