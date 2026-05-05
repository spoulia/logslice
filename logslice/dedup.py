"""Deduplication utilities for log entries."""

from __future__ import annotations

import hashlib
from typing import Iterable, Iterator


def _entry_key(entry: dict, fields: list[str] | None = None) -> str:
    """Compute a deduplication key for a log entry.

    If *fields* is provided, only those fields contribute to the key.
    Otherwise the full message (and level, if present) is used.
    """
    if fields:
        parts = [str(entry.get(f, "")) for f in sorted(fields)]
    else:
        parts = [
            entry.get("message", ""),
            entry.get("level", ""),
        ]
    raw = "\x00".join(parts).encode()
    return hashlib.md5(raw).hexdigest()


def dedup_entries(
    entries: Iterable[dict],
    fields: list[str] | None = None,
    keep: str = "first",
) -> Iterator[dict]:
    """Yield deduplicated log entries.

    Parameters
    ----------
    entries:
        Iterable of parsed log entry dicts.
    fields:
        Optional list of field names to use for key comparison.
        Defaults to ``["message", "level"]``.
    keep:
        ``"first"`` (default) keeps the first occurrence;
        ``"last"`` keeps the last occurrence.

    Yields
    ------
    dict
        Unique log entries in original order (for *keep="first"*) or
        reverse-deduped order re-reversed (for *keep="last"*).
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    if keep == "first":
        seen: set[str] = set()
        for entry in entries:
            key = _entry_key(entry, fields)
            if key not in seen:
                seen.add(key)
                yield entry
    else:
        # keep last: collect all, then deduplicate in reverse
        all_entries = list(entries)
        seen_last: set[str] = set()
        result: list[dict] = []
        for entry in reversed(all_entries):
            key = _entry_key(entry, fields)
            if key not in seen_last:
                seen_last.add(key)
                result.append(entry)
        yield from reversed(result)
