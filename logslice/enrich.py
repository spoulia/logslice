"""Entry enrichment — attach derived or external fields to log entries."""

from __future__ import annotations

import re
import socket
from typing import Any, Callable, Dict, Iterable, List, Optional

EnrichFn = Callable[[Dict[str, Any]], Dict[str, Any]]


def enrich_with_hostname(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Add the local hostname under the 'host' key if not already present."""
    if "host" not in entry:
        entry = dict(entry)
        entry["host"] = socket.gethostname()
    return entry


def enrich_with_static(fields: Dict[str, Any]) -> EnrichFn:
    """Return an enricher that merges *fields* into every entry (no overwrite)."""

    def _enrich(entry: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(fields)
        merged.update(entry)  # entry values win
        return merged

    return _enrich


def enrich_with_derived(
    source_field: str,
    dest_field: str,
    transform: Callable[[Any], Any],
) -> EnrichFn:
    """Return an enricher that derives *dest_field* from *source_field* via *transform*."""

    def _enrich(entry: Dict[str, Any]) -> Dict[str, Any]:
        if source_field in entry:
            entry = dict(entry)
            entry[dest_field] = transform(entry[source_field])
        return entry

    return _enrich


def enrich_with_regex(
    source_field: str,
    pattern: str,
    dest_fields: Optional[List[str]] = None,
) -> EnrichFn:
    """Extract named groups (or positional groups mapped to *dest_fields*) from a field."""
    compiled = re.compile(pattern)

    def _enrich(entry: Dict[str, Any]) -> Dict[str, Any]:
        value = entry.get(source_field, "")
        m = compiled.search(str(value))
        if not m:
            return entry
        entry = dict(entry)
        if m.groupdict():
            entry.update(m.groupdict())
        elif dest_fields:
            for key, val in zip(dest_fields, m.groups()):
                entry[key] = val
        return entry

    return _enrich


def apply_enrichers(
    entries: Iterable[Dict[str, Any]],
    enrichers: List[EnrichFn],
) -> List[Dict[str, Any]]:
    """Apply a sequence of enricher functions to every entry."""
    result = []
    for entry in entries:
        for fn in enrichers:
            entry = fn(entry)
        result.append(entry)
    return result
