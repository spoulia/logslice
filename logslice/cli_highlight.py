"""CLI integration for highlighted log output."""

import argparse
import sys
from typing import List

from logslice.highlight import highlight_entry, supports_color
from logslice.core import parse_log_line


def add_highlight_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'highlight' subcommand."""
    parser = subparsers.add_parser(
        "highlight",
        help="Print log lines with terminal color highlighting",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Log file to read (defaults to stdin)",
    )
    parser.add_argument(
        "--pattern", "-p",
        default=None,
        help="Pattern to highlight within messages",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output",
    )
    parser.set_defaults(func=run_highlight)


def run_highlight(args: argparse.Namespace) -> None:
    """Execute the highlight subcommand."""
    use_color = not args.no_color and supports_color()

    if args.file:
        try:
            source = open(args.file, "r", encoding="utf-8")
        except OSError as exc:
            print(f"logslice highlight: error opening file: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        source = sys.stdin

    try:
        for raw_line in source:
            line = raw_line.rstrip("\n")
            entry = parse_log_line(line)
            print(highlight_entry(entry, pattern=args.pattern, use_color=use_color))
    finally:
        if args.file:
            source.close()
