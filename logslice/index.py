"""Entry indexing for fast field-based lookups."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, Iterator, List, Optional


class Index:
    """In-memory inverted index over log entries keyed by field values."""

    def __init__(self, fields: Optional[List[str]] = None) -> None:
        self._fields: List[str] = fields or ["level", "source"]
        # field -> value -> list of entry positions
        self._index: Dict[str, Dict[Any, List[int]]] = {
            f: defaultdict(list) for f in self._fields
        }
        self._entries: List[dict] = []

    # ------------------------------------------------------------------
    def add(self, entry: dict) -> int:
        """Append *entry* to the index and return its position."""
        pos = len(self._entries)
        self._entries.append(entry)
        for field in self._fields:
            value = entry.get(field)
            if value is not None:
                self._index[field][value].append(pos)
        return pos

    def add_many(self, entries: Iterable[dict]) -> None:
        """Index an iterable of entries."""
        for entry in entries:
            self.add(entry)

    # ------------------------------------------------------------------
    def lookup(self, field: str, value: Any) -> List[dict]:
        """Return all entries where *field* equals *value*."""
        if field not in self._index:
            return []
        positions = self._index[field].get(value, [])
        return [self._entries[p] for p in positions]

    def lookup_many(self, field: str, values: Iterable[Any]) -> List[dict]:
        """Return entries matching any of *values* for *field*."""
        seen: set = set()
        result: List[dict] = []
        for value in values:
            for entry in self.lookup(field, value):
                eid = id(entry)
                if eid not in seen:
                    seen.add(eid)
                    result.append(entry)
        return result

    # ------------------------------------------------------------------
    def all_values(self, field: str) -> List[Any]:
        """Return the distinct indexed values for *field*."""
        return list(self._index.get(field, {}).keys())

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[dict]:
        return iter(self._entries)

    # ------------------------------------------------------------------
    def clear(self) -> None:
        """Remove all entries and reset the index."""
        self._entries.clear()
        for field in self._fields:
            self._index[field] = defaultdict(list)


def build_index(entries: Iterable[dict], fields: Optional[List[str]] = None) -> Index:
    """Convenience wrapper: create and populate an :class:`Index`."""
    idx = Index(fields=fields)
    idx.add_many(entries)
    return idx
