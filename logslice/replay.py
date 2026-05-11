"""Replay log entries at their original speed or a scaled rate."""

import time
from typing import Callable, Iterable, Iterator, Optional

from logslice.core import LogEntry


def _delta_seconds(prev: Optional[dict], current: dict) -> float:
    """Return the time difference in seconds between two entries."""
    if prev is None:
        return 0.0
    t1 = prev.get("timestamp")
    t2 = current.get("timestamp")
    if t1 is None or t2 is None:
        return 0.0
    try:
        diff = (t2 - t1).total_seconds()
        return max(diff, 0.0)
    except (AttributeError, TypeError):
        return 0.0


def replay_entries(
    entries: Iterable[dict],
    speed: float = 1.0,
    callback: Optional[Callable[[dict], None]] = None,
    max_delay: float = 5.0,
) -> Iterator[dict]:
    """Yield entries with inter-arrival delays scaled by *speed*.

    Args:
        entries:   Iterable of log entry dicts.
        speed:     Playback multiplier. 2.0 = twice as fast, 0.5 = half speed.
        callback:  Optional function called with each entry before yielding.
        max_delay: Upper bound (seconds) on any single sleep to avoid stalls.

    Yields:
        Each log entry dict in order.
    """
    if speed <= 0:
        raise ValueError(f"speed must be > 0, got {speed!r}")

    prev: Optional[dict] = None
    for entry in entries:
        delta = _delta_seconds(prev, entry)
        sleep_time = min(delta / speed, max_delay)
        if sleep_time > 0:
            time.sleep(sleep_time)
        if callback is not None:
            callback(entry)
        yield entry
        prev = entry


def collect_replay(
    entries: Iterable[dict],
    speed: float = 1.0,
    max_delay: float = 5.0,
) -> list:
    """Convenience wrapper that drains *replay_entries* into a list."""
    return list(replay_entries(entries, speed=speed, max_delay=max_delay))
