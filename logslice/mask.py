"""Field masking utilities for logslice.

Provides functions to partially or fully mask field values in log entries,
useful for hiding sensitive data while preserving log structure.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional


_MASK_CHAR = "*"


def mask_value(value: str, keep_start: int = 0, keep_end: int = 0, char: str = _MASK_CHAR) -> str:
    """Partially mask a string value.

    Args:
        value:      The string to mask.
        keep_start: Number of leading characters to preserve.
        keep_end:   Number of trailing characters to preserve.
        char:       Character used for masking.

    Returns:
        Masked string of the same length as *value*.
    """
    if not isinstance(value, str):
        value = str(value)
    n = len(value)
    keep_start = max(0, min(keep_start, n))
    keep_end = max(0, min(keep_end, n - keep_start))
    masked_len = n - keep_start - keep_end
    if masked_len <= 0:
        return value
    return value[:keep_start] + char * masked_len + value[n - keep_end:] if keep_end else value[:keep_start] + char * masked_len


def mask_field(
    entry: Dict[str, Any],
    field: str,
    keep_start: int = 0,
    keep_end: int = 0,
    char: str = _MASK_CHAR,
) -> Dict[str, Any]:
    """Return a copy of *entry* with *field* masked."""
    if field not in entry:
        return dict(entry)
    result = dict(entry)
    result[field] = mask_value(str(entry[field]), keep_start=keep_start, keep_end=keep_end, char=char)
    return result


def mask_fields(
    entry: Dict[str, Any],
    fields: List[str],
    keep_start: int = 0,
    keep_end: int = 0,
    char: str = _MASK_CHAR,
) -> Dict[str, Any]:
    """Return a copy of *entry* with all listed *fields* masked."""
    result = dict(entry)
    for field in fields:
        if field in result:
            result[field] = mask_value(str(result[field]), keep_start=keep_start, keep_end=keep_end, char=char)
    return result


def mask_entries(
    entries: Iterable[Dict[str, Any]],
    fields: List[str],
    keep_start: int = 0,
    keep_end: int = 0,
    char: str = _MASK_CHAR,
) -> List[Dict[str, Any]]:
    """Apply field masking to a sequence of log entries."""
    return [
        mask_fields(entry, fields, keep_start=keep_start, keep_end=keep_end, char=char)
        for entry in entries
    ]
