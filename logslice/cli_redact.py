"""CLI sub-command: redact — stream log lines with sensitive data masked."""

import argparse
import sys
from typing import List, Optional

from logslice.core import parse_log_line
from logslice.redact import DEFAULT_PATTERNS, redact_entry
from logslice.formatters import get_formatter


def add_redact_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "redact",
        help="Mask sensitive data in log lines before output.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Log file to read (default: stdin).",
    )
    p.add_argument(
        "--fields",
        nargs="+",
        metavar="FIELD",
        default=[],
        help="Field names to redact entirely.",
    )
    p.add_argument(
        "--patterns",
        nargs="+",
        metavar="REGEX",
        default=None,
        help="Custom regex patterns to redact (overrides built-in defaults).",
    )
    p.add_argument(
        "--placeholder",
        default="[REDACTED]",
        help="Replacement text for redacted values.",
    )
    p.add_argument(
        "--format",
        choices=["plain", "json", "csv"],
        default="plain",
        dest="fmt",
        help="Output format.",
    )
    p.set_defaults(func=run_redact)


def run_redact(args: argparse.Namespace) -> None:
    patterns: Optional[List[str]] = args.patterns  # None → use defaults
    formatter = get_formatter(args.fmt)

    source = open(args.file) if args.file != "-" else sys.stdin  # noqa: WPS515
    try:
        for raw_line in source:
            entry = parse_log_line(raw_line.rstrip("\n"))
            entry = redact_entry(
                entry,
                patterns=patterns,
                fields=args.fields or None,
                placeholder=args.placeholder,
            )
            print(formatter(entry))
    finally:
        if args.file != "-":
            source.close()
