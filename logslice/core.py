"""Core log filtering engine for logslice.

Supports both structured (JSON) and unstructured (plain text) log formats.
Provides time-range filtering, keyword search, and log level filtering.
"""

import re
import json
import sys
from datetime import datetime
from typing import Iterator, Optional

# Common timestamp patterns found in unstructured logs
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-01-15T13:45:00Z or 2024-01-15T13:45:00.123Z
    re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)'),
    # Common syslog: 2024-01-15 13:45:00
    re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)'),
    # Apache/nginx: 15/Jan/2024:13:45:00
    re.compile(r'(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})'),
]

TIMESTAMP_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%d/%b/%Y:%H:%M:%S",
]

LOG_LEVEL_FIELDS = ["level", "severity", "log_level", "loglevel"]


def parse_timestamp(value: str) -> Optional[datetime]:
    """Attempt to parse a timestamp string using known formats."""
    for fmt in TIMESTAMP_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            # Strip timezone info for naive comparison
            return dt.replace(tzinfo=None)
        except ValueError:
            continue
    return None


def extract_timestamp_from_line(line: str) -> Optional[datetime]:
    """Extract the first recognizable timestamp from a plain-text log line."""
    for pattern in TIMESTAMP_PATTERNS:
        match = pattern.search(line)
        if match:
            ts = parse_timestamp(match.group(1))
            if ts:
                return ts
    return None


def parse_log_line(line: str) -> tuple[Optional[datetime], Optional[str], str]:
    """Parse a log line and return (timestamp, level, raw_line).

    Handles both JSON-structured logs and plain-text logs.
    """
    stripped = line.strip()
    if not stripped:
        return None, None, line

    # Try JSON first
    if stripped.startswith('{'):
        try:
            obj = json.loads(stripped)
            ts = None
            for ts_key in ("timestamp", "time", "@timestamp", "ts", "date"):
                if ts_key in obj:
                    ts = parse_timestamp(str(obj[ts_key]))
                    if ts:
                        break

            level = None
            for lvl_key in LOG_LEVEL_FIELDS:
                if lvl_key in obj:
                    level = str(obj[lvl_key]).upper()
                    break

            return ts, level, line
        except json.JSONDecodeError:
            pass

    # Fall back to unstructured parsing
    ts = extract_timestamp_from_line(stripped)
    level = extract_level_from_line(stripped)
    return ts, level, line


def extract_level_from_line(line: str) -> Optional[str]:
    """Heuristically extract log level from a plain-text log line."""
    level_pattern = re.compile(
        r'\b(DEBUG|INFO|NOTICE|WARN(?:ING)?|ERROR|CRITICAL|FATAL|TRACE)\b',
        re.IGNORECASE
    )
    match = level_pattern.search(line)
    if match:
        lvl = match.group(1).upper()
        return "WARNING" if lvl == "WARN" else lvl
    return None


def filter_logs(
    lines: Iterator[str],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    levels: Optional[list[str]] = None,
    keyword: Optional[str] = None,
    keyword_regex: bool = False,
) -> Iterator[str]:
    """Filter log lines based on time range, log level, and keyword.

    Args:
        lines:         Iterable of raw log line strings.
        start:         Include lines at or after this timestamp.
        end:           Include lines at or before this timestamp.
        levels:        List of log levels to include (e.g. ['ERROR', 'WARN']).
        keyword:       Substring or regex pattern to match against each line.
        keyword_regex: If True, treat keyword as a compiled regex.

    Yields:
        Matching log lines (with original newlines preserved).
    """
    normalized_levels = {l.upper() for l in levels} if levels else None
    kw_pattern = re.compile(keyword, re.IGNORECASE) if keyword and keyword_regex else None

    for line in lines:
        ts, level, raw = parse_log_line(line)

        # Time-range filtering
        if start and ts and ts < start:
            continue
        if end and ts and ts > end:
            continue

        # Level filtering
        if normalized_levels and level and level not in normalized_levels:
            continue

        # Keyword filtering
        if keyword:
            if kw_pattern:
                if not kw_pattern.search(raw):
                    continue
            else:
                if keyword.lower() not in raw.lower():
                    continue

        yield raw
