"""Tail-like functionality for logslice: follow a log file in real time."""

import time
import os
from typing import Callable, Optional

from logslice.core import extract_timestamp_from_line, extract_level_from_line, parse_log_line


def tail_file(
    filepath: str,
    callback: Callable[[dict], None],
    poll_interval: float = 0.25,
    min_level: Optional[str] = None,
    pattern: Optional[str] = None,
) -> None:
    """Follow *filepath*, calling *callback* for each new log entry.

    Blocks indefinitely until a KeyboardInterrupt is received.

    Args:
        filepath: Path to the log file to follow.
        callback: Called with a parsed log entry dict for every matching line.
        poll_interval: Seconds between file-read attempts when no new data.
        min_level: If given, skip entries below this severity level.
        pattern: If given, skip entries whose raw line does not contain this string.
    """
    from logslice.filters import filter_by_level, filter_by_pattern

    level_order = ["debug", "info", "warning", "error", "critical"]

    def _passes(entry: dict, raw_line: str) -> bool:
        if pattern and pattern.lower() not in raw_line.lower():
            return False
        if min_level:
            lvl = (entry.get("level") or "").lower()
            min_lvl = min_level.lower()
            if lvl in level_order and min_lvl in level_order:
                if level_order.index(lvl) < level_order.index(min_lvl):
                    return False
        return True

    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        # Seek to end so we only see new lines
        fh.seek(0, os.SEEK_END)
        try:
            while True:
                line = fh.readline()
                if not line:
                    time.sleep(poll_interval)
                    continue
                line = line.rstrip("\n")
                entry = parse_log_line(line)
                if _passes(entry, line):
                    callback(entry)
        except KeyboardInterrupt:
            pass
