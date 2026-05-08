"""Correlate log entries by a shared field value (e.g. request_id, trace_id)."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional


def group_by_correlation_id(
    entries: Iterable[dict],
    field: str = "request_id",
) -> Dict[str, List[dict]]:
    """Group entries by the value of *field*.

    Entries that lack the field are collected under the empty-string key.

    Args:
        entries: Iterable of parsed log entry dicts.
        field:   The field name to correlate on.

    Returns:
        Mapping from field value -> list of entries (in original order).
    """
    groups: Dict[str, List[dict]] = defaultdict(list)
    for entry in entries:
        key = str(entry.get(field, ""))
        groups[key].append(entry)
    return dict(groups)


def get_correlated(
    entries: Iterable[dict],
    value: str,
    field: str = "request_id",
) -> List[dict]:
    """Return all entries whose *field* matches *value*.

    Args:
        entries: Iterable of parsed log entry dicts.
        value:   The correlation value to look up.
        field:   The field name to correlate on.

    Returns:
        List of matching entries, preserving original order.
    """
    return [e for e in entries if str(e.get(field, "")) == value]


def first_and_last(
    entries: List[dict],
) -> tuple[Optional[dict], Optional[dict]]:
    """Return the first and last entries in a correlated group.

    Args:
        entries: Non-empty list of log entry dicts.

    Returns:
        Tuple of (first_entry, last_entry).  Both are None if *entries* is empty.
    """
    if not entries:
        return None, None
    return entries[0], entries[-1]


def summarise_group(entries: List[dict]) -> dict:
    """Produce a lightweight summary dict for a correlated group.

    Returns a dict with:
        count       – total number of entries
        levels      – set of distinct log levels seen
        has_error   – True if any entry has level ERROR or CRITICAL
        first_ts    – timestamp of the first entry (or None)
        last_ts     – timestamp of the last entry (or None)
    """
    levels = {str(e.get("level", "")).upper() for e in entries}
    first, last = first_and_last(entries)
    return {
        "count": len(entries),
        "levels": levels,
        "has_error": bool(levels & {"ERROR", "CRITICAL"}),
        "first_ts": first.get("timestamp") if first else None,
        "last_ts": last.get("timestamp") if last else None,
    }
