"""Label / tag log entries based on field values or patterns."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional


def label_by_pattern(
    entries: Iterable[dict],
    pattern: str,
    label: str,
    field: str = "message",
    label_key: str = "label",
) -> List[dict]:
    """Attach *label* to every entry whose *field* matches *pattern*."""
    rx = re.compile(pattern)
    result = []
    for entry in entries:
        e = dict(entry)
        if rx.search(str(e.get(field, ""))):
            existing = e.get(label_key)
            if isinstance(existing, list):
                if label not in existing:
                    existing.append(label)
            elif existing is not None:
                e[label_key] = [existing, label] if existing != label else [existing]
            else:
                e[label_key] = label
        result.append(e)
    return result


def label_by_field(
    entries: Iterable[dict],
    mapping: Dict[str, str],
    label_key: str = "label",
) -> List[dict]:
    """Attach a label when an entry contains a specific field equal to a value.

    *mapping* maps ``"field=value"`` strings to label strings.
    """
    parsed = {}
    for kv, lbl in mapping.items():
        if "=" in kv:
            f, v = kv.split("=", 1)
            parsed[(f.strip(), v.strip())] = lbl

    result = []
    for entry in entries:
        e = dict(entry)
        for (field, value), label in parsed.items():
            if str(e.get(field, "")) == value:
                existing = e.get(label_key)
                if isinstance(existing, list):
                    if label not in existing:
                        existing.append(label)
                elif existing is not None:
                    e[label_key] = [existing, label] if existing != label else [existing]
                else:
                    e[label_key] = label
        result.append(e)
    return result


def clear_labels(entries: Iterable[dict], label_key: str = "label") -> List[dict]:
    """Remove the label field from all entries."""
    return [{k: v for k, v in e.items() if k != label_key} for e in entries]


def filter_by_label(
    entries: Iterable[dict],
    label: str,
    label_key: str = "label",
) -> List[dict]:
    """Return only entries that carry *label*."""
    result = []
    for entry in entries:
        val = entry.get(label_key)
        if val == label or (isinstance(val, list) and label in val):
            result.append(entry)
    return result
