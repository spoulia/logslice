"""Output writing utilities for logslice."""

import sys
from typing import Any, Dict, Iterable, Optional, TextIO

from logslice.formatters import get_formatter


def write_entries(
    entries: Iterable[Dict[str, Any]],
    fmt: str = "plain",
    dest: Optional[TextIO] = None,
    csv_header: bool = True,
) -> int:
    """
    Write log entries to a destination file-like object.

    Args:
        entries: Iterable of parsed log entry dicts.
        fmt: Output format ('plain', 'json', 'csv').
        dest: Output stream. Defaults to sys.stdout.
        csv_header: Whether to write a CSV header row when fmt='csv'.

    Returns:
        Number of entries written.
    """
    if dest is None:
        dest = sys.stdout

    formatter = get_formatter(fmt)
    count = 0

    if fmt == "csv" and csv_header:
        dest.write("timestamp,level,message\n")

    for entry in entries:
        line = formatter(entry)
        dest.write(line + "\n")
        count += 1

    return count


def write_entries_to_file(
    entries: Iterable[Dict[str, Any]],
    filepath: str,
    fmt: str = "plain",
    csv_header: bool = True,
) -> int:
    """
    Write log entries to a file.

    Args:
        entries: Iterable of parsed log entry dicts.
        filepath: Path to the output file.
        fmt: Output format ('plain', 'json', 'csv').
        csv_header: Whether to write a CSV header row when fmt='csv'.

    Returns:
        Number of entries written.
    """
    with open(filepath, "w", encoding="utf-8") as fh:
        return write_entries(entries, fmt=fmt, dest=fh, csv_header=csv_header)
