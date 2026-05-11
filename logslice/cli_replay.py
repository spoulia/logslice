"""CLI sub-command: replay — stream log entries at original or scaled speed."""

import argparse
import sys
from typing import List

from logslice.core import parse_log_line
from logslice.formatters import get_formatter
from logslice.replay import replay_entries


def add_replay_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "replay",
        help="Stream log entries with timing delays that mirror the original.",
    )
    p.add_argument("file", help="Log file to replay (use '-' for stdin).")
    p.add_argument(
        "--speed",
        type=float,
        default=1.0,
        metavar="FACTOR",
        help="Playback speed multiplier (default: 1.0).",
    )
    p.add_argument(
        "--max-delay",
        type=float,
        default=5.0,
        metavar="SECS",
        help="Maximum sleep between entries in seconds (default: 5.0).",
    )
    p.add_argument(
        "--format",
        choices=["plain", "json", "csv"],
        default="plain",
        dest="fmt",
        help="Output format (default: plain).",
    )
    p.set_defaults(func=run_replay)


def _read_entries(path: str) -> List[dict]:
    if path == "-":
        lines = sys.stdin.readlines()
    else:
        with open(path) as fh:
            lines = fh.readlines()
    return [parse_log_line(line) for line in lines if line.strip()]


def run_replay(args: argparse.Namespace) -> None:
    entries = _read_entries(args.file)
    formatter = get_formatter(args.fmt)

    def _print(entry: dict) -> None:
        print(formatter(entry), flush=True)

    for _ in replay_entries(
        entries,
        speed=args.speed,
        max_delay=args.max_delay,
        callback=_print,
    ):
        pass
