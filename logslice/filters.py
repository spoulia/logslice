"""Additional filtering utilities for logslice."""

import re
from typing import Optional, List, Dict, Any


def filter_by_level(
    entries: List[Dict[str, Any]],
    min_level: Optional[str] = None,
    levels: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Filter log entries by severity level.

    Args:
        entries: List of parsed log entry dicts.
        min_level: Minimum level to include (e.g. 'WARNING' includes WARNING, ERROR, CRITICAL).
        levels: Explicit list of levels to include.

    Returns:
        Filtered list of entries.
    """
    LEVEL_ORDER = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    if levels is not None:
        allowed = {lvl.upper() for lvl in levels}
        return [e for e in entries if (e.get("level") or "").upper() in allowed]

    if min_level is not None:
        min_level = min_level.upper()
        if min_level not in LEVEL_ORDER:
            raise ValueError(f"Unknown log level: {min_level!r}")
        min_index = LEVEL_ORDER.index(min_level)
        allowed = set(LEVEL_ORDER[min_index:])
        return [e for e in entries if (e.get("level") or "").upper() in allowed]

    return entries


def filter_by_pattern(
    entries: List[Dict[str, Any]],
    pattern: str,
    field: str = "message",
    invert: bool = False,
) -> List[Dict[str, Any]]:
    """Filter log entries whose field matches a regex pattern.

    Args:
        entries: List of parsed log entry dicts.
        pattern: Regular expression pattern to match.
        field: Entry field to search in (default: 'message').
        invert: If True, exclude matching entries instead.

    Returns:
        Filtered list of entries.
    """
    compiled = re.compile(pattern)

    def matches(entry: Dict[str, Any]) -> bool:
        value = str(entry.get(field) or "")
        return bool(compiled.search(value))

    if invert:
        return [e for e in entries if not matches(e)]
    return [e for e in entries if matches(e)]


def filter_by_fields(
    entries: List[Dict[str, Any]],
    **field_values: str,
) -> List[Dict[str, Any]]:
    """Filter entries where structured fields match exact values.

    Args:
        entries: List of parsed log entry dicts.
        **field_values: Keyword arguments mapping field names to expected values.

    Returns:
        Filtered list of entries.
    """
    def entry_matches(entry: Dict[str, Any]) -> bool:
        extra = entry.get("extra") or {}
        for key, expected in field_values.items():
            actual = entry.get(key) or extra.get(key)
            if str(actual) != str(expected):
                return False
        return True

    return [e for e in entries if entry_matches(e)]
