"""Tests for logslice.sort."""

from __future__ import annotations

import pytest

from logslice.sort import iter_sorted, sort_entries, stable_sort_entries


def _e(ts=None, level="INFO", msg="hello", **kwargs):
    entry = {"level": level, "message": msg}
    if ts is not None:
        entry["timestamp"] = ts
    entry.update(kwargs)
    return entry


class TestSortEntries:
    def test_empty_returns_empty(self):
        assert sort_entries([]) == []

    def test_sorted_ascending_by_timestamp(self):
        entries = [_e("2024-01-03"), _e("2024-01-01"), _e("2024-01-02")]
        result = sort_entries(entries)
        assert [e["timestamp"] for e in result] == [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
        ]

    def test_sorted_descending_by_timestamp(self):
        entries = [_e("2024-01-01"), _e("2024-01-03"), _e("2024-01-02")]
        result = sort_entries(entries, reverse=True)
        assert result[0]["timestamp"] == "2024-01-03"
        assert result[-1]["timestamp"] == "2024-01-01"

    def test_sort_by_custom_field(self):
        entries = [_e(msg="b"), _e(msg="a"), _e(msg="c")]
        result = sort_entries(entries, field="message")
        assert [e["message"] for e in result] == ["a", "b", "c"]

    def test_missing_field_placed_last_by_default(self):
        entries = [_e("2024-01-02"), _e(), _e("2024-01-01")]
        result = sort_entries(entries)
        assert result[-1].get("timestamp") is None

    def test_missing_field_placed_first_when_flag_false(self):
        entries = [_e("2024-01-02"), _e(), _e("2024-01-01")]
        result = sort_entries(entries, missing_last=False)
        assert result[0].get("timestamp") is None

    def test_original_list_not_mutated(self):
        entries = [_e("2024-01-03"), _e("2024-01-01")]
        original_order = [e["timestamp"] for e in entries]
        sort_entries(entries)
        assert [e["timestamp"] for e in entries] == original_order

    def test_single_entry_returned_as_is(self):
        e = _e("2024-01-01")
        assert sort_entries([e]) == [e]


class TestStableSortEntries:
    def test_single_field_behaves_like_sort_entries(self):
        entries = [_e("2024-01-03"), _e("2024-01-01"), _e("2024-01-02")]
        result = stable_sort_entries(entries, fields=["timestamp"])
        assert [e["timestamp"] for e in result] == [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
        ]

    def test_multi_field_sort(self):
        entries = [
            _e("2024-01-01", level="WARNING"),
            _e("2024-01-01", level="ERROR"),
            _e("2024-01-01", level="INFO"),
        ]
        result = stable_sort_entries(entries, fields=["timestamp", "level"])
        levels = [e["level"] for e in result]
        assert levels == ["ERROR", "INFO", "WARNING"]

    def test_default_fields_is_timestamp(self):
        entries = [_e("2024-01-02"), _e("2024-01-01")]
        result = stable_sort_entries(entries)
        assert result[0]["timestamp"] == "2024-01-01"

    def test_reverse_multi_field(self):
        entries = [_e("2024-01-01"), _e("2024-01-03"), _e("2024-01-02")]
        result = stable_sort_entries(entries, reverse=True)
        assert result[0]["timestamp"] == "2024-01-03"


class TestIterSorted:
    def test_yields_entries_in_order(self):
        entries = [_e("2024-01-03"), _e("2024-01-01"), _e("2024-01-02")]
        result = list(iter_sorted(entries))
        assert result[0]["timestamp"] == "2024-01-01"

    def test_returns_iterator(self):
        import types
        entries = [_e("2024-01-01")]
        assert isinstance(iter_sorted(entries), types.GeneratorType)
