"""Annotate log entries with arbitrary key-value metadata."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Iterator, List, Optional


def annotate_entry(
    entry: Dict[str, Any],
    annotations: Dict[str, Any],
    *,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """Return a copy of *entry* with *annotations* merged in.

    If *overwrite* is False (default) existing keys are preserved.
    """
    result = dict(entry)
    for key, value in annotations.items():
        if overwrite or key not in result:
            result[key] = value
    return result


def annotate_entries(
    entries: Iterable[Dict[str, Any]],
    annotations: Dict[str, Any],
    *,
    overwrite: bool = False,
) -> Iterator[Dict[str, Any]]:
    """Yield entries each annotated with *annotations*."""
    for entry in entries:
        yield annotate_entry(entry, annotations, overwrite=overwrite)


def annotate_by_pattern(
    entries: Iterable[Dict[str, Any]],
    pattern: str,
    annotations: Dict[str, Any],
    *,
    field: str = "message",
    overwrite: bool = False,
) -> Iterator[Dict[str, Any]]:
    """Annotate entries whose *field* matches *pattern* (regex)."""
    compiled = re.compile(pattern)
    for entry in entries:
        value = str(entry.get(field, ""))
        if compiled.search(value):
            yield annotate_entry(entry, annotations, overwrite=overwrite)
        else:
            yield dict(entry)


def annotate_by_level(
    entries: Iterable[Dict[str, Any]],
    level_annotations: Dict[str, Dict[str, Any]],
    *,
    level_field: str = "level",
    overwrite: bool = False,
) -> Iterator[Dict[str, Any]]:
    """Annotate entries based on their log level.

    *level_annotations* maps level strings (case-insensitive) to dicts of
    key-value pairs to add when that level is matched.
    """
    normalised = {k.lower(): v for k, v in level_annotations.items()}
    for entry in entries:
        level = str(entry.get(level_field, "")).lower()
        extra = normalised.get(level, {})
        if extra:
            yield annotate_entry(entry, extra, overwrite=overwrite)
        else:
            yield dict(entry)
