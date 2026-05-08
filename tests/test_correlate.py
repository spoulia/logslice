"""Tests for logslice.correlate."""

from __future__ import annotations

import pytest

from logslice.correlate import (
    first_and_last,
    get_correlated,
    group_by_correlation_id,
    summarise_group,
)


def _e(request_id: str, level: str = "INFO", ts: str = "2024-01-01T00:00:00") -> dict:
    return {"request_id": request_id, "level": level, "timestamp": ts, "message": "msg"}


class TestGroupByCorrelationId:
    def test_groups_by_default_field(self):
        entries = [_e("abc"), _e("abc"), _e("xyz")]
        groups = group_by_correlation_id(entries)
        assert len(groups["abc"]) == 2
        assert len(groups["xyz"]) == 1

    def test_missing_field_goes_to_empty_key(self):
        entries = [{"message": "no id"}]
        groups = group_by_correlation_id(entries)
        assert "" in groups
        assert len(groups[""]) == 1

    def test_custom_field(self):
        entries = [
            {"trace_id": "t1", "message": "a"},
            {"trace_id": "t1", "message": "b"},
            {"trace_id": "t2", "message": "c"},
        ]
        groups = group_by_correlation_id(entries, field="trace_id")
        assert sorted(groups.keys()) == ["t1", "t2"]

    def test_preserves_order(self):
        entries = [_e("r", ts=f"2024-01-01T00:00:0{i}") for i in range(5)]
        groups = group_by_correlation_id(entries)
        assert [e["timestamp"] for e in groups["r"]] == [
            f"2024-01-01T00:00:0{i}" for i in range(5)
        ]

    def test_empty_input(self):
        assert group_by_correlation_id([]) == {}


class TestGetCorrelated:
    def test_returns_matching_entries(self):
        entries = [_e("a"), _e("b"), _e("a")]
        result = get_correlated(entries, "a")
        assert len(result) == 2
        assert all(e["request_id"] == "a" for e in result)

    def test_no_match_returns_empty(self):
        entries = [_e("a"), _e("b")]
        assert get_correlated(entries, "z") == []

    def test_custom_field(self):
        entries = [{"session": "s1"}, {"session": "s2"}]
        result = get_correlated(entries, "s1", field="session")
        assert len(result) == 1


class TestFirstAndLast:
    def test_single_entry(self):
        e = _e("r")
        first, last = first_and_last([e])
        assert first is e
        assert last is e

    def test_multiple_entries(self):
        entries = [_e("r", ts=f"2024-01-01T00:00:0{i}") for i in range(3)]
        first, last = first_and_last(entries)
        assert first["timestamp"] == "2024-01-01T00:00:00"
        assert last["timestamp"] == "2024-01-01T00:00:02"

    def test_empty_returns_none_pair(self):
        assert first_and_last([]) == (None, None)


class TestSummariseGroup:
    def test_count(self):
        entries = [_e("r") for _ in range(4)]
        assert summarise_group(entries)["count"] == 4

    def test_has_error_true(self):
        entries = [_e("r", level="INFO"), _e("r", level="ERROR")]
        assert summarise_group(entries)["has_error"] is True

    def test_has_error_false(self):
        entries = [_e("r", level="INFO"), _e("r", level="DEBUG")]
        assert summarise_group(entries)["has_error"] is False

    def test_critical_counts_as_error(self):
        entries = [_e("r", level="CRITICAL")]
        assert summarise_group(entries)["has_error"] is True

    def test_levels_set(self):
        entries = [_e("r", level="info"), _e("r", level="warn")]
        summary = summarise_group(entries)
        assert summary["levels"] == {"INFO", "WARN"}

    def test_timestamps(self):
        entries = [_e("r", ts="2024-01-01T00:00:00"), _e("r", ts="2024-01-01T01:00:00")]
        summary = summarise_group(entries)
        assert summary["first_ts"] == "2024-01-01T00:00:00"
        assert summary["last_ts"] == "2024-01-01T01:00:00"

    def test_empty_group(self):
        summary = summarise_group([])
        assert summary["count"] == 0
        assert summary["first_ts"] is None
        assert summary["last_ts"] is None
