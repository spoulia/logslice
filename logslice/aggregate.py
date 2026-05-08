"""Log aggregation: group and count entries by a field or time bucket."""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _bucket_timestamp(ts: Optional[datetime], interval: str) -> Optional[str]:
    """Truncate a datetime to the given interval bucket ('minute', 'hour', 'day')."""
    if ts is None:
        return None
    ts = ts.astimezone(timezone.utc)
    if interval == "minute":
        return ts.strftime("%Y-%m-%dT%H:%M")
    if interval == "hour":
        return ts.strftime("%Y-%m-%dT%H")
    if interval == "day":
        return ts.strftime("%Y-%m-%d")
    raise ValueError(f"Unknown interval: {interval!r}. Choose 'minute', 'hour', or 'day'.")


def group_by_field(entries: List[Dict[str, Any]], field: str) -> Dict[str, List[Dict[str, Any]]]:
    """Group log entries by the value of a given field.

    Entries missing the field are grouped under the key '<missing>'.
    """
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        key = str(entry.get(field, "<missing>"))
        groups[key].append(entry)
    return dict(groups)


def count_by_field(entries: List[Dict[str, Any]], field: str) -> Dict[str, int]:
    """Return a mapping of field-value -> occurrence count."""
    counts: Dict[str, int] = defaultdict(int)
    for entry in entries:
        key = str(entry.get(field, "<missing>"))
        counts[key] += 1
    return dict(counts)


def group_by_time(entries: List[Dict[str, Any]], interval: str = "hour") -> Dict[str, List[Dict[str, Any]]]:
    """Group log entries into time buckets of the given interval.

    Entries without a timestamp are grouped under '<no-timestamp>'.
    """
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        ts = entry.get("timestamp")
        bucket = _bucket_timestamp(ts, interval) if isinstance(ts, datetime) else "<no-timestamp>"
        groups[bucket or "<no-timestamp>"].append(entry)
    return dict(groups)


def count_by_time(entries: List[Dict[str, Any]], interval: str = "hour") -> Dict[str, int]:
    """Return a mapping of time-bucket -> occurrence count."""
    groups = group_by_time(entries, interval)
    return {bucket: len(items) for bucket, items in groups.items()}
