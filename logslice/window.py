"""Time-window slicing: extract log entries within a rolling or fixed window."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Iterator, List, Optional


def _as_datetime(ts) -> Optional[datetime]:
    """Coerce a timestamp value to datetime, or return None."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, (int, float)):
        return datetime.utcfromtimestamp(ts)
    return None


def window_between(
    entries: Iterable[dict],
    start: datetime,
    end: datetime,
) -> Iterator[dict]:
    """Yield entries whose timestamp falls within [start, end] (inclusive)."""
    for entry in entries:
        ts = _as_datetime(entry.get("timestamp"))
        if ts is not None and start <= ts <= end:
            yield entry


def window_last(
    entries: Iterable[dict],
    seconds: float,
    reference: Optional[datetime] = None,
) -> List[dict]:
    """Return entries from the last *seconds* seconds relative to *reference*.

    If *reference* is None the current UTC time is used.
    """
    if seconds < 0:
        raise ValueError("seconds must be non-negative")
    ref = reference if reference is not None else datetime.utcnow()
    cutoff = ref - timedelta(seconds=seconds)
    return list(window_between(entries, cutoff, ref))


def window_around(
    entries: Iterable[dict],
    anchor: datetime,
    before: float = 60.0,
    after: float = 60.0,
) -> List[dict]:
    """Return entries within *before* seconds before and *after* seconds after *anchor*."""
    if before < 0 or after < 0:
        raise ValueError("before and after must be non-negative")
    start = anchor - timedelta(seconds=before)
    end = anchor + timedelta(seconds=after)
    return list(window_between(entries, start, end))


def split_into_windows(
    entries: Iterable[dict],
    window_seconds: float,
) -> List[List[dict]]:
    """Partition entries into consecutive fixed-size time buckets.

    Entries without a valid timestamp are skipped.  The returned list is
    ordered chronologically; each inner list contains entries belonging to
    the same bucket.
    """
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    buckets: dict[int, List[dict]] = {}
    for entry in entries:
        ts = _as_datetime(entry.get("timestamp"))
        if ts is None:
            continue
        bucket_index = int(ts.timestamp() // window_seconds)
        buckets.setdefault(bucket_index, []).append(entry)
    return [buckets[k] for k in sorted(buckets)]
