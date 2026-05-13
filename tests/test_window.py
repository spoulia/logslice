"""Tests for logslice.window."""

from datetime import datetime, timedelta

import pytest

from logslice.window import (
    window_between,
    window_last,
    window_around,
    split_into_windows,
)


def _e(ts: datetime, message: str = "msg") -> dict:
    return {"timestamp": ts, "message": message, "level": "INFO"}


NOW = datetime(2024, 6, 1, 12, 0, 0)
ENTRIES = [
    _e(NOW - timedelta(seconds=120), "old"),
    _e(NOW - timedelta(seconds=60), "mid"),
    _e(NOW, "now"),
    _e(NOW + timedelta(seconds=30), "future"),
]


class TestWindowBetween:
    def test_returns_only_entries_in_range(self):
        start = NOW - timedelta(seconds=70)
        end = NOW + timedelta(seconds=5)
        result = list(window_between(ENTRIES, start, end))
        assert len(result) == 2
        assert result[0]["message"] == "mid"
        assert result[1]["message"] == "now"

    def test_inclusive_boundaries(self):
        result = list(window_between(ENTRIES, NOW, NOW))
        assert len(result) == 1
        assert result[0]["message"] == "now"

    def test_no_entries_in_empty_range(self):
        far_future = NOW + timedelta(hours=1)
        result = list(window_between(ENTRIES, far_future, far_future))
        assert result == []

    def test_entry_without_timestamp_skipped(self):
        mixed = ENTRIES + [{"message": "no-ts", "level": "DEBUG"}]
        result = list(window_between(mixed, NOW - timedelta(seconds=200), NOW + timedelta(seconds=200)))
        assert all("timestamp" in e for e in result)
        assert len(result) == len(ENTRIES)

    def test_float_timestamp_accepted(self):
        entry = {"timestamp": NOW.timestamp(), "message": "float-ts"}
        result = list(window_between([entry], NOW - timedelta(seconds=1), NOW + timedelta(seconds=1)))
        assert len(result) == 1


class TestWindowLast:
    def test_returns_recent_entries(self):
        result = window_last(ENTRIES, seconds=90, reference=NOW)
        messages = [e["message"] for e in result]
        assert "mid" in messages
        assert "now" in messages
        assert "old" not in messages

    def test_zero_seconds_returns_only_exact_match(self):
        result = window_last(ENTRIES, seconds=0, reference=NOW)
        assert all(e["timestamp"] == NOW for e in result)

    def test_negative_seconds_raises(self):
        with pytest.raises(ValueError):
            window_last(ENTRIES, seconds=-1, reference=NOW)

    def test_future_entries_excluded(self):
        result = window_last(ENTRIES, seconds=10, reference=NOW)
        assert all(e["timestamp"] <= NOW for e in result)


class TestWindowAround:
    def test_symmetric_window(self):
        result = window_around(ENTRIES, anchor=NOW, before=65, after=35)
        messages = [e["message"] for e in result]
        assert "mid" in messages
        assert "now" in messages
        assert "future" in messages
        assert "old" not in messages

    def test_negative_before_raises(self):
        with pytest.raises(ValueError):
            window_around(ENTRIES, anchor=NOW, before=-1)

    def test_negative_after_raises(self):
        with pytest.raises(ValueError):
            window_around(ENTRIES, anchor=NOW, after=-1)


class TestSplitIntoWindows:
    def test_splits_into_correct_number_of_buckets(self):
        buckets = split_into_windows(ENTRIES, window_seconds=70)
        assert len(buckets) >= 2

    def test_each_bucket_is_non_empty(self):
        buckets = split_into_windows(ENTRIES, window_seconds=60)
        assert all(len(b) > 0 for b in buckets)

    def test_zero_window_raises(self):
        with pytest.raises(ValueError):
            split_into_windows(ENTRIES, window_seconds=0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError):
            split_into_windows(ENTRIES, window_seconds=-10)

    def test_entry_without_timestamp_skipped(self):
        mixed = list(ENTRIES) + [{"message": "no-ts"}]
        buckets = split_into_windows(mixed, window_seconds=3600)
        total = sum(len(b) for b in buckets)
        assert total == len(ENTRIES)
