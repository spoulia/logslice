"""High-level summary command integration for logslice."""

import json
import sys
from typing import List, Dict, Any, Optional, TextIO

from logslice.stats import compute_stats, format_stats_text


def print_summary(
    entries: List[Dict[str, Any]],
    output_format: str = "text",
    out: Optional[TextIO] = None,
) -> None:
    """Print a summary of log entries to the given output stream.

    Args:
        entries: Parsed log entry dicts.
        output_format: One of 'text' or 'json'.
        out: Output stream; defaults to sys.stdout.
    """
    if out is None:
        out = sys.stdout

    stats = compute_stats(entries)

    if output_format == "json":
        out.write(json.dumps(stats, default=str, indent=2))
        out.write("\n")
    else:
        out.write(format_stats_text(stats))
        out.write("\n")


def summary_from_file(
    filepath: str,
    output_format: str = "text",
    out: Optional[TextIO] = None,
) -> None:
    """Read a JSONL log file, parse entries, and print a summary.

    Each line in the file should be a JSON object representing a log entry.

    Args:
        filepath: Path to the JSONL log file.
        output_format: 'text' or 'json'.
        out: Output stream; defaults to sys.stdout.
    """
    entries: List[Dict[str, Any]] = []
    with open(filepath, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict):
                    entries.append(entry)
            except json.JSONDecodeError:
                pass

    print_summary(entries, output_format=output_format, out=out)
