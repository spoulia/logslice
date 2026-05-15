"""Snapshot: capture and restore a point-in-time view of log entries."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, Iterator, List, Optional


SnapshotEntry = Dict[str, object]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_snapshot(
    entries: Iterable[SnapshotEntry],
    label: Optional[str] = None,
) -> dict:
    """Wrap *entries* in a snapshot envelope."""
    items = list(entries)
    return {
        "label": label or "",
        "created_at": _utcnow(),
        "count": len(items),
        "entries": items,
    }


def save_snapshot(snapshot: dict, path: str) -> str:
    """Persist *snapshot* as JSON to *path*. Returns the resolved path."""
    path = os.path.abspath(path)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, default=str)
    return path


def load_snapshot(path: str) -> dict:
    """Load a snapshot from *path*. Raises ``ValueError`` on bad format."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if "entries" not in data:
        raise ValueError(f"Invalid snapshot file (missing 'entries'): {path}")
    return data


def restore_entries(snapshot: dict) -> Iterator[SnapshotEntry]:
    """Yield the log entries stored inside *snapshot*."""
    yield from snapshot.get("entries", [])


def diff_snapshots(
    old: dict,
    new: dict,
    key: str = "message",
) -> Dict[str, List[SnapshotEntry]]:
    """Return entries added / removed between *old* and *new* snapshots."""
    old_keys = {e.get(key) for e in old.get("entries", [])}
    new_keys = {e.get(key) for e in new.get("entries", [])}
    added = [e for e in new.get("entries", []) if e.get(key) not in old_keys]
    removed = [e for e in old.get("entries", []) if e.get(key) not in new_keys]
    return {"added": added, "removed": removed}
