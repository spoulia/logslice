"""CLI subcommand handler for the 'summary' command."""

import sys
from typing import List, Optional

from logslice.core import parse_log_line
from logslice.summary import print_summary


def add_summary_subparser(subparsers) -> None:
    """Register the 'summary' subcommand on an existing subparsers object."""
    parser = subparsers.add_parser(
        "summary",
        help="Print statistics and a summary of log entries.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Log file to summarise (default: stdin).",
    )
    parser.add_argument(
        "--format",
        dest="summary_format",
        choices=["text", "json"],
        default="text",
        help="Output format for the summary (default: text).",
    )
    parser.set_defaults(func=run_summary)


def run_summary(args) -> int:
    """Execute the summary subcommand.

    Reads log lines from a file or stdin, parses them, and prints statistics.

    Returns:
        Exit code (0 on success, 1 on error).
    """
    entries = []

    try:
        if args.file == "-":
            lines = sys.stdin.readlines()
        else:
            with open(args.file, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
    except OSError as exc:
        print(f"logslice summary: error reading file: {exc}", file=sys.stderr)
        return 1

    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue
        entry = parse_log_line(line)
        if entry:
            entries.append(entry)

    print_summary(entries, output_format=args.summary_format)
    return 0
