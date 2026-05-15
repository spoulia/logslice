"""Split a stream of log entries into chunks by count, size, or time boundary."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Iterator, List


def split_by_count(entries: Iterable[dict], chunk_size: int) -> Iterator[List[dict]]:
    """Yield successive chunks of *chunk_size* entries."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    chunk: List[dict] = []
    for entry in entries:
        chunk.append(entry)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def split_by_field(entries: Iterable[dict], field: str) -> Iterator[List[dict]]:
    """Yield a new chunk every time *field* value changes (run-length encoding)."""
    chunk: List[dict] = []
    _sentinel = object()
    current_value = _sentinel
    for entry in entries:
        value = entry.get(field)
        if current_value is _sentinel:
            current_value = value
        if value != current_value:
            if chunk:
                yield chunk
            chunk = [entry]
            current_value = value
        else:
            chunk.append(entry)
    if chunk:
        yield chunk


def split_by_time(entries: Iterable[dict], interval_seconds: float) -> Iterator[List[dict]]:
    """Yield chunks where all entries fall within *interval_seconds* of the first
    entry in that chunk.  Entries without a timestamp are placed in the current chunk.
    """
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be > 0")
    delta = timedelta(seconds=interval_seconds)
    chunk: List[dict] = []
    window_start: datetime | None = None
    for entry in entries:
        ts = entry.get("timestamp")
        if ts is None or window_start is None:
            chunk.append(entry)
            if ts is not None and window_start is None:
                window_start = ts
        elif ts - window_start <= delta:
            chunk.append(entry)
        else:
            yield chunk
            chunk = [entry]
            window_start = ts
    if chunk:
        yield chunk


def split_entries(
    entries: Iterable[dict],
    *,
    count: int | None = None,
    field: str | None = None,
    interval_seconds: float | None = None,
) -> Iterator[List[dict]]:
    """Unified split dispatcher.  Exactly one keyword argument must be supplied."""
    provided = sum(x is not None for x in (count, field, interval_seconds))
    if provided != 1:
        raise ValueError("Exactly one of count, field, or interval_seconds must be given")
    if count is not None:
        yield from split_by_count(entries, count)
    elif field is not None:
        yield from split_by_field(entries, field)
    else:
        yield from split_by_time(entries, interval_seconds)  # type: ignore[arg-type]
