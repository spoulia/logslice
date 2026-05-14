"""Merge multiple sorted log entry streams into a single time-ordered sequence."""

from __future__ import annotations

import heapq
from typing import Iterable, Iterator, List, Optional, Tuple

from logslice.core import parse_timestamp


def _sort_key(entry: dict) -> Tuple:
    """Return a sortable key for an entry based on its timestamp."""
    ts = entry.get("timestamp") or entry.get("time") or ""
    dt = parse_timestamp(ts) if ts else None
    # Entries without a timestamp sort to the end
    return (0, dt) if dt is not None else (1, None)


def merge_sorted(
    *streams: Iterable[dict],
    key: Optional[str] = None,
) -> Iterator[dict]:
    """Merge multiple entry iterables in chronological order.

    Uses a heap to perform an efficient k-way merge.  Entries that lack a
    parseable timestamp are appended after all timestamped entries.

    Args:
        *streams: Any number of iterables yielding log entry dicts.
        key: Optional field name to use as the sort key.  Defaults to
             ``timestamp`` / ``time`` auto-detection.

    Yields:
        Log entry dicts in ascending timestamp order.
    """
    heap: list = []
    delayed: List[dict] = []
    counter = 0  # tie-breaker so dicts are never compared directly

    def _push(entry: dict) -> None:
        nonlocal counter
        if key:
            raw = entry.get(key, "")
            dt = parse_timestamp(raw) if raw else None
        else:
            ts = entry.get("timestamp") or entry.get("time") or ""
            dt = parse_timestamp(ts) if ts else None

        if dt is None:
            delayed.append(entry)
        else:
            heapq.heappush(heap, (dt, counter, entry))
            counter += 1

    iterators = [iter(s) for s in streams]
    for it in iterators:
        for entry in it:
            _push(entry)

    while heap:
        _, _, entry = heapq.heappop(heap)
        yield entry

    yield from delayed


def merge_files(
    file_paths: Iterable[str],
    parser=None,
) -> Iterator[dict]:
    """Read multiple log files and merge them in timestamp order.

    Args:
        file_paths: Paths to log files.
        parser: Optional callable ``(line: str) -> dict``.  Defaults to
                :func:`logslice.core.parse_log_line`.

    Yields:
        Merged log entry dicts.
    """
    from logslice.core import parse_log_line  # local import to avoid cycles

    _parse = parser or parse_log_line

    def _stream(path: str) -> Iterator[dict]:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line:
                    yield _parse(line)

    streams = [_stream(p) for p in file_paths]
    yield from merge_sorted(*streams)
