"""Command-line interface for logslice."""

import sys
import argparse
from typing import List, Optional

from logslice.core import filter_logs
from logslice.filters import filter_by_level, filter_by_pattern, filter_by_fields
from logslice.formatters import get_formatter
from logslice.output import write_entries, write_entries_to_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering utility for structured and unstructured logs.",
    )
    parser.add_argument("input", nargs="?", help="Input log file (default: stdin)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument(
        "--start", help="Start timestamp (ISO 8601 or log-native format)"
    )
    parser.add_argument("--end", help="End timestamp (ISO 8601 or log-native format)")
    parser.add_argument(
        "--level",
        help="Minimum log level to include (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        metavar="LEVEL",
        help="Explicit list of levels to include",
    )
    parser.add_argument(
        "--grep", metavar="PATTERN", help="Regex pattern to match in message field"
    )
    parser.add_argument(
        "--grep-field",
        default="message",
        metavar="FIELD",
        help="Field to apply --grep pattern to (default: message)",
    )
    parser.add_argument(
        "--invert", action="store_true", help="Invert --grep match (exclude matches)"
    )
    parser.add_argument(
        "--field",
        nargs=2,
        action="append",
        metavar=("KEY", "VALUE"),
        dest="fields",
        help="Filter by exact field value (repeatable)",
    )
    parser.add_argument(
        "--format",
        choices=["plain", "json", "csv"],
        default="plain",
        help="Output format (default: plain)",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.input:
        with open(args.input, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    else:
        lines = sys.stdin.readlines()

    entries = filter_logs(lines, start=args.start, end=args.end)

    if args.level or args.levels:
        entries = filter_by_level(entries, min_level=args.level, levels=args.levels)

    if args.grep:
        entries = filter_by_pattern(
            entries, pattern=args.grep, field=args.grep_field, invert=args.invert
        )

    if args.fields:
        field_kwargs = {k: v for k, v in args.fields}
        entries = filter_by_fields(entries, **field_kwargs)

    formatter = get_formatter(args.format)

    if args.output:
        write_entries_to_file(entries, args.output, formatter)
    else:
        write_entries(entries, sys.stdout, formatter)

    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
