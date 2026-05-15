"""Tests for logslice.split."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.split import (
    split_by_count,
    split_by_field,
    split_by_time,
    split_entries,
)


def _e(msg: str = "x", level: str = "info", ts: datetime | None = None) -> dict:
    entry: dict = {"message": msg, "level": level}
    if ts is not None:
        entry["timestamp"] = ts
    return entry


def _ts(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# split_by_count
# ---------------------------------------------------------------------------

class TestSplitByCount:
    def test_even_split(self):
        entries = [_e() for _ in range(6)]
        chunks = list(split_by_count(entries, 2))
        assert len(chunks) == 3
        assert all(len(c) == 2 for c in chunks)

    def test_remainder_chunk(self):
        entries = [_e() for _ in range(5)]
        chunks = list(split_by_count(entries, 3))
        assert len(chunks) == 2
        assert len(chunks[-1]) == 2

    def test_empty_input_yields_nothing(self):
        assert list(split_by_count([], 10)) == []

    def test_chunk_size_zero_raises(self):
        with pytest.raises(ValueError):
            list(split_by_count([_e()], 0))

    def test_chunk_size_one(self):
        entries = [_e() for _ in range(4)]
        chunks = list(split_by_count(entries, 1))
        assert len(chunks) == 4


# ---------------------------------------------------------------------------
# split_by_field
# ---------------------------------------------------------------------------

class TestSplitByField:
    def test_groups_consecutive_equal_values(self):
        entries = [
            _e(level="info"), _e(level="info"),
            _e(level="error"),
            _e(level="info"),
        ]
        chunks = list(split_by_field(entries, "level"))
        assert len(chunks) == 3

    def test_all_same_value_is_one_chunk(self):
        entries = [_e(level="debug") for _ in range(5)]
        assert len(list(split_by_field(entries, "level"))) == 1

    def test_empty_input_yields_nothing(self):
        assert list(split_by_field([], "level")) == []

    def test_missing_field_treated_as_none(self):
        entries = [{"message": "a"}, {"message": "b"}, {"level": "info"}]
        chunks = list(split_by_field(entries, "level"))
        # first two have None, third has 'info' — should produce 2 chunks
        assert len(chunks) == 2


# ---------------------------------------------------------------------------
# split_by_time
# ---------------------------------------------------------------------------

class TestSplitByTime:
    def test_entries_within_window_grouped(self):
        entries = [
            _e(ts=_ts(10, 0)),
            _e(ts=_ts(10, 1)),
            _e(ts=_ts(10, 2)),
        ]
        chunks = list(split_by_time(entries, 180))
        assert len(chunks) == 1

    def test_entries_outside_window_split(self):
        entries = [
            _e(ts=_ts(10, 0)),
            _e(ts=_ts(10, 5)),
        ]
        chunks = list(split_by_time(entries, 60))
        assert len(chunks) == 2

    def test_zero_interval_raises(self):
        with pytest.raises(ValueError):
            list(split_by_time([], 0))

    def test_no_timestamp_stays_in_current_chunk(self):
        entries = [_e(ts=_ts(10, 0)), {"message": "no-ts"}, _e(ts=_ts(10, 0))]
        chunks = list(split_by_time(entries, 10))
        assert sum(len(c) for c in chunks) == 3


# ---------------------------------------------------------------------------
# split_entries dispatcher
# ---------------------------------------------------------------------------

class TestSplitEntries:
    def test_count_dispatches_correctly(self):
        entries = [_e() for _ in range(4)]
        chunks = list(split_entries(entries, count=2))
        assert len(chunks) == 2

    def test_field_dispatches_correctly(self):
        entries = [_e(level="info"), _e(level="error")]
        chunks = list(split_entries(entries, field="level"))
        assert len(chunks) == 2

    def test_interval_dispatches_correctly(self):
        entries = [_e(ts=_ts(1)), _e(ts=_ts(3))]
        chunks = list(split_entries(entries, interval_seconds=30))
        assert len(chunks) == 2

    def test_no_args_raises(self):
        with pytest.raises(ValueError):
            list(split_entries([]))

    def test_two_args_raises(self):
        with pytest.raises(ValueError):
            list(split_entries([], count=2, field="level"))
