"""Partition log entries into named buckets based on field values or patterns."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Callable, Dict, Iterable, List, Optional, Tuple

Entry = Dict[str, object]
PartitionMap = Dict[str, List[Entry]]


def partition_by_field(
    entries: Iterable[Entry],
    field: str,
    default_key: str = "__unset__",
) -> PartitionMap:
    """Group entries into buckets keyed by the value of *field*."""
    buckets: PartitionMap = defaultdict(list)
    for entry in entries:
        key = str(entry.get(field, default_key))
        buckets[key].append(entry)
    return dict(buckets)


def partition_by_pattern(
    entries: Iterable[Entry],
    patterns: List[Tuple[str, str]],
    field: str = "message",
    default_key: str = "other",
) -> PartitionMap:
    """Group entries by the first matching regex pattern.

    *patterns* is a list of ``(label, regex)`` pairs checked in order.
    Entries that match no pattern are placed under *default_key*.
    """
    compiled = [(label, re.compile(rx)) for label, rx in patterns]
    buckets: PartitionMap = defaultdict(list)
    for entry in entries:
        text = str(entry.get(field, ""))
        matched = False
        for label, rx in compiled:
            if rx.search(text):
                buckets[label].append(entry)
                matched = True
                break
        if not matched:
            buckets[default_key].append(entry)
    return dict(buckets)


def partition_by_predicate(
    entries: Iterable[Entry],
    predicates: List[Tuple[str, Callable[[Entry], bool]]],
    default_key: str = "other",
) -> PartitionMap:
    """Group entries using callable predicates checked in order."""
    buckets: PartitionMap = defaultdict(list)
    for entry in entries:
        matched = False
        for label, predicate in predicates:
            if predicate(entry):
                buckets[label].append(entry)
                matched = True
                break
        if not matched:
            buckets[default_key].append(entry)
    return dict(buckets)


def merge_partitions(*maps: PartitionMap) -> PartitionMap:
    """Merge multiple partition maps, concatenating lists for shared keys."""
    result: PartitionMap = defaultdict(list)
    for pm in maps:
        for key, entries in pm.items():
            result[key].extend(entries)
    return dict(result)


def partition_sizes(pm: PartitionMap) -> Dict[str, int]:
    """Return a dict mapping each bucket key to its entry count."""
    return {k: len(v) for k, v in pm.items()}
