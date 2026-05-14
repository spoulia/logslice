"""Field and message truncation utilities for log entries."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional

_ELLIPSIS = "..."


def truncate_string(value: str, max_length: int, ellipsis: str = _ELLIPSIS) -> str:
    """Truncate *value* to *max_length* characters, appending *ellipsis* if cut.

    If *max_length* is less than or equal to zero, an empty string is returned.
    """
    if max_length <= 0:
        return ""
    if len(value) <= max_length:
        return value
    cut = max(0, max_length - len(ellipsis))
    return value[:cut] + ellipsis


def truncate_field(
    entry: Dict[str, Any],
    field: str,
    max_length: int,
    ellipsis: str = _ELLIPSIS,
) -> Dict[str, Any]:
    """Return a copy of *entry* with *field* truncated to *max_length* chars."""
    if field not in entry:
        return dict(entry)
    result = dict(entry)
    raw = result[field]
    if isinstance(raw, str):
        result[field] = truncate_string(raw, max_length, ellipsis)
    return result


def truncate_fields(
    entry: Dict[str, Any],
    fields: Dict[str, int],
    ellipsis: str = _ELLIPSIS,
) -> Dict[str, Any]:
    """Return a copy of *entry* with each field in *fields* truncated.

    *fields* maps field name -> max_length.
    """
    result = dict(entry)
    for field, max_length in fields.items():
        if field in result and isinstance(result[field], str):
            result[field] = truncate_string(result[field], max_length, ellipsis)
    return result


def truncate_message(
    entry: Dict[str, Any],
    max_length: int,
    message_key: str = "message",
    ellipsis: str = _ELLIPSIS,
) -> Dict[str, Any]:
    """Convenience wrapper that truncates the *message_key* field."""
    return truncate_field(entry, message_key, max_length, ellipsis)


def truncate_entries(
    entries: Iterable[Dict[str, Any]],
    fields: Dict[str, int],
    ellipsis: str = _ELLIPSIS,
) -> Iterator[Dict[str, Any]]:
    """Yield entries with each field in *fields* truncated to its max length."""
    for entry in entries:
        yield truncate_fields(entry, fields, ellipsis)
