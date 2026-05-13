"""CLI sub-command: watch a log file and print new lines, handling rotation."""

from __future__ import annotations

import argparse
import time
import sys
from typing import Optional

from logslice.rotate import detect_rotation, read_new_lines, _file_inode, _file_size
from logslice.highlight import highlight_entry, supports_color
from logslice.core import parse_log_line


def add_rotate_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "rotate",
        help="Watch a log file for new lines, handling log rotation gracefully.",
    )
    p.add_argument("file", help="Path to the log file to watch.")
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 1.0).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    p.add_argument(
        "--pattern",
        default=None,
        metavar="REGEX",
        help="Highlight lines matching this pattern.",
    )
    p.set_defaults(func=run_rotate)


def run_rotate(args: argparse.Namespace) -> None:  # pragma: no cover
    """Poll *args.file* for new content, printing each new line."""
    path: str = args.file
    interval: float = args.interval
    use_color: bool = supports_color() and not args.no_color
    pattern: Optional[str] = args.pattern

    position: int = _file_size(path)
    last_inode = _file_inode(path)
    last_size = position

    try:
        while True:
            rotated = detect_rotation(path, last_inode, last_size)
            if rotated:
                sys.stderr.write(f"[logslice] rotation detected for {path}\n")
                position = 0
                last_inode = _file_inode(path)

            lines, position = read_new_lines(path, position)
            last_size = _file_size(path)

            for raw in lines:
                if not raw:
                    continue
                entry = parse_log_line(raw)
                if use_color:
                    print(highlight_entry(entry, pattern=pattern))
                else:
                    print(entry.get("message", raw))

            time.sleep(interval)
    except KeyboardInterrupt:
        pass
