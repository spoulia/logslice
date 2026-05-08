"""Export log entries to various file formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, Iterable, List

LOG_ENTRY = Dict[str, Any]


def export_to_json(entries: List[LOG_ENTRY], indent: int = 2) -> str:
    """Serialise entries to a JSON string."""
    return json.dumps(entries, indent=indent, default=str)


def export_to_csv(entries: List[LOG_ENTRY], fields: List[str] | None = None) -> str:
    """Serialise entries to a CSV string.

    If *fields* is omitted the union of all keys found in the entries is used,
    sorted alphabetically so the output is deterministic.
    """
    if not entries:
        return ""

    if fields is None:
        all_keys: set[str] = set()
        for e in entries:
            all_keys.update(e.keys())
        fields = sorted(all_keys)

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    for entry in entries:
        writer.writerow({f: entry.get(f, "") for f in fields})
    return buf.getvalue()


def export_to_ndjson(entries: Iterable[LOG_ENTRY]) -> str:
    """Serialise entries as newline-delimited JSON (one object per line)."""
    lines = [json.dumps(e, default=str) for e in entries]
    return "\n".join(lines) + ("\n" if lines else "")


def export_entries(entries: List[LOG_ENTRY], fmt: str, **kwargs: Any) -> str:
    """Dispatch to the appropriate exporter based on *fmt*.

    Supported formats: ``json``, ``csv``, ``ndjson``.
    """
    fmt = fmt.lower()
    if fmt == "json":
        return export_to_json(entries, **kwargs)
    if fmt == "csv":
        return export_to_csv(entries, **kwargs)
    if fmt == "ndjson":
        return export_to_ndjson(entries)
    raise ValueError(f"Unsupported export format: {fmt!r}")
