"""Tests for logslice.partition."""

from __future__ import annotations

import pytest

from logslice.partition import (
    merge_partitions,
    partition_by_field,
    partition_by_pattern,
    partition_by_predicate,
    partition_sizes,
)


def _e(level: str = "info", message: str = "hello", **kw) -> dict:
    return {"level": level, "message": message, **kw}


# ---------------------------------------------------------------------------
# partition_by_field
# ---------------------------------------------------------------------------

class TestPartitionByField:
    def test_groups_by_level(self):
        entries = [_e("info"), _e("error"), _e("info")]
        pm = partition_by_field(entries, "level")
        assert len(pm["info"]) == 2
        assert len(pm["error"]) == 1

    def test_missing_field_uses_default_key(self):
        entries = [_e(), {"message": "no level"}]
        pm = partition_by_field(entries, "level", default_key="unknown")
        assert "unknown" in pm
        assert len(pm["unknown"]) == 1

    def test_empty_input_returns_empty_dict(self):
        assert partition_by_field([], "level") == {}

    def test_single_entry(self):
        pm = partition_by_field([_e("warn")], "level")
        assert list(pm.keys()) == ["warn"]


# ---------------------------------------------------------------------------
# partition_by_pattern
# ---------------------------------------------------------------------------

class TestPartitionByPattern:
    def test_first_matching_pattern_wins(self):
        entries = [_e(message="connection timeout"), _e(message="disk full")]
        patterns = [("network", r"timeout|connect"), ("disk", r"disk")]
        pm = partition_by_pattern(entries, patterns)
        assert len(pm["network"]) == 1
        assert len(pm["disk"]) == 1

    def test_unmatched_goes_to_default(self):
        entries = [_e(message="something else")]
        pm = partition_by_pattern(entries, [("net", r"timeout")], default_key="misc")
        assert "misc" in pm
        assert len(pm["misc"]) == 1

    def test_empty_patterns_all_go_to_default(self):
        entries = [_e(), _e()]
        pm = partition_by_pattern(entries, [])
        assert sum(len(v) for v in pm.values()) == 2

    def test_custom_field(self):
        entries = [{"level": "error", "source": "db"}]
        pm = partition_by_pattern(entries, [("database", r"db")], field="source")
        assert "database" in pm


# ---------------------------------------------------------------------------
# partition_by_predicate
# ---------------------------------------------------------------------------

class TestPartitionByPredicate:
    def test_predicate_routes_entry(self):
        entries = [_e("error"), _e("info"), _e("error")]
        preds = [("errors", lambda e: e.get("level") == "error")]
        pm = partition_by_predicate(entries, preds)
        assert len(pm["errors"]) == 2
        assert len(pm["other"]) == 1

    def test_no_predicates_all_default(self):
        entries = [_e(), _e()]
        pm = partition_by_predicate(entries, [])
        assert len(pm["other"]) == 2


# ---------------------------------------------------------------------------
# merge_partitions
# ---------------------------------------------------------------------------

class TestMergePartitions:
    def test_combines_shared_keys(self):
        pm1 = {"info": [_e("info")]}
        pm2 = {"info": [_e("info")], "error": [_e("error")]}
        merged = merge_partitions(pm1, pm2)
        assert len(merged["info"]) == 2
        assert len(merged["error"]) == 1

    def test_empty_merge_returns_empty(self):
        assert merge_partitions() == {}


# ---------------------------------------------------------------------------
# partition_sizes
# ---------------------------------------------------------------------------

def test_partition_sizes():
    pm = {"info": [_e(), _e()], "error": [_e()]}
    sizes = partition_sizes(pm)
    assert sizes == {"info": 2, "error": 1}


def test_partition_sizes_empty():
    assert partition_sizes({}) == {}
