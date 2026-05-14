"""Sorting utilities for log entries."""

from __future__ import annotations

from typing import Callable, Iterable, Iterator, List, Optional


_MISSING = object()


def _sort_key_func(
    field: str,
    reverse: bool = False,
    missing_last: bool = True,
) -> Callable[[dict], tuple]:
    """Return a key function that extracts *field* from an entry."""

    def key(entry: dict) -> tuple:
        value = entry.get(field, _MISSING)
        if value is _MISSING:
            # Push missing values to the end (or front when reversed).
            sentinel = (1,) if missing_last else (0,)
            return sentinel + (None,)
        return (0,) + (value,)

    return key


def sort_entries(
    entries: Iterable[dict],
    field: str = "timestamp",
    reverse: bool = False,
    missing_last: bool = True,
) -> List[dict]:
    """Return *entries* sorted by *field*.

    Parameters
    ----------
    entries:
        Iterable of log-entry dicts.
    field:
        The entry key to sort by.  Defaults to ``"timestamp"``.
    reverse:
        When ``True`` sort in descending order.
    missing_last:
        When ``True`` (default) entries that lack *field* are placed at the
        end regardless of *reverse*.
    """
    key = _sort_key_func(field, reverse=reverse, missing_last=missing_last)
    return sorted(entries, key=key, reverse=reverse)


def stable_sort_entries(
    entries: Iterable[dict],
    fields: Optional[List[str]] = None,
    reverse: bool = False,
) -> List[dict]:
    """Sort *entries* by multiple *fields* with a stable sort.

    Each field is applied as a successive sort key (right-to-left), which
    together produce a multi-key stable sort.
    """
    if fields is None:
        fields = ["timestamp"]

    result = list(entries)
    for field in reversed(fields):
        key = _sort_key_func(field, reverse=reverse)
        result.sort(key=key, reverse=reverse)
    return result


def iter_sorted(
    entries: Iterable[dict],
    field: str = "timestamp",
    reverse: bool = False,
) -> Iterator[dict]:
    """Yield *entries* in sorted order.  Convenience wrapper around
    :func:`sort_entries` that returns an iterator."""
    yield from sort_entries(entries, field=field, reverse=reverse)
