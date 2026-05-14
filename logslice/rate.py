"""Rate limiting and throughput measurement for log entry streams."""

from __future__ import annotations

import time
from collections import deque
from typing import Iterable, Iterator, List

from logslice.core import LogEntry


def _now() -> float:
    return time.monotonic()


def measure_rate(
    entries: Iterable[LogEntry],
    window_seconds: float = 60.0,
) -> Iterator[tuple[LogEntry, float]]:
    """Yield (entry, current_rate) pairs where rate is entries/second
    computed over a rolling *window_seconds* window."""
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")

    timestamps: deque[float] = deque()
    for entry in entries:
        now = _now()
        timestamps.append(now)
        cutoff = now - window_seconds
        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()
        rate = len(timestamps) / window_seconds
        yield entry, rate


def throttle_entries(
    entries: Iterable[LogEntry],
    max_rate: float,
) -> Iterator[LogEntry]:
    """Yield entries while enforcing at most *max_rate* entries per second.
    Excess entries are dropped (not buffered)."""
    if max_rate <= 0:
        raise ValueError("max_rate must be positive")

    interval = 1.0 / max_rate
    last_emit = _now() - interval
    for entry in entries:
        now = _now()
        if now - last_emit >= interval:
            last_emit = now
            yield entry


def rate_summary(entries: List[LogEntry]) -> dict:
    """Return a dict with throughput statistics for a pre-collected list."""
    if not entries:
        return {"count": 0, "duration_seconds": 0.0, "rate_per_second": 0.0}

    timestamps = [
        e.get("timestamp") for e in entries if e.get("timestamp") is not None
    ]
    count = len(entries)
    if len(timestamps) < 2:
        return {"count": count, "duration_seconds": 0.0, "rate_per_second": 0.0}

    try:
        from logslice.core import parse_timestamp

        first = parse_timestamp(str(timestamps[0]))
        last = parse_timestamp(str(timestamps[-1]))
        if first and last:
            duration = (last - first).total_seconds()
        else:
            duration = 0.0
    except Exception:
        duration = 0.0

    rate = (count / duration) if duration > 0 else 0.0
    return {"count": count, "duration_seconds": round(duration, 3), "rate_per_second": round(rate, 4)}
