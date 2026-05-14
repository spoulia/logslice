"""CLI sub-command: alert — watch a log file and fire alerts on matching entries."""

from __future__ import annotations

import argparse
import sys

from logslice.alert import build_condition, evaluate_alerts, file_handler, stdout_handler
from logslice.core import parse_log_line


def add_alert_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "alert",
        help="Scan log entries and trigger alerts on matching conditions.",
    )
    p.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Log file to read (default: stdin).",
    )
    p.add_argument(
        "--condition",
        default="error",
        help="Alert condition: 'error', 'warning', 'any', or a regex pattern (default: error).",
    )
    p.add_argument(
        "--output",
        default=None,
        help="File to write triggered alerts to (default: stdout).",
    )
    p.add_argument(
        "--count",
        action="store_true",
        help="Print only the number of triggered alerts.",
    )


def _open_input(path: str):
    """Open a log file for reading, or return stdin for '-'.

    Returns a tuple of (file_object, is_stdin) so the caller knows
    whether to close the file when done.
    """
    if path == "-":
        return sys.stdin, True
    try:
        return open(path, encoding="utf-8"), False  # noqa: WPS515
    except OSError as exc:
        raise OSError(exc) from exc


def run_alert(args: argparse.Namespace) -> int:
    handler = file_handler(args.output) if args.output else stdout_handler

    try:
        lines, is_stdin = _open_input(args.input)
    except OSError as exc:
        print(f"logslice alert: {exc}", file=sys.stderr)
        return 1

    try:
        entries = (parse_log_line(line) for line in lines)
        triggered = evaluate_alerts(entries, args.condition, handler=handler if not args.count else lambda _e: None)
    finally:
        if not is_stdin:
            lines.close()

    if args.count:
        print(len(triggered))

    return 0
