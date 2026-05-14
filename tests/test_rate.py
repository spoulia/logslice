"""Tests for logslice.rate."""

from __future__ import annotations

import time
from typing import List

import pytest

from logslice.rate import measure_rate, throttle_entries, rate_summary


def _entries(n: int, level: str = "INFO") -> List[dict]:
    return [{"message": f"msg {i}", "level": level} for i in range(n)]


# ---------------------------------------------------------------------------
# measure_rate
# ---------------------------------------------------------------------------

class TestMeasureRate:
    def test_yields_same_count(self):
        entries = _entries(5)
        results = list(measure_rate(entries, window_seconds=10.0))
        assert len(results) == 5

    def test_yields_tuples_with_rate(self):
        entries = _entries(3)
        for entry, rate in measure_rate(entries, window_seconds=10.0):
            assert isinstance(rate, float)
            assert rate >= 0.0

    def test_entry_identity_preserved(self):
        entries = _entries(2)
        results = list(measure_rate(entries, window_seconds=10.0))
        assert results[0][0]["message"] == "msg 0"
        assert results[1][0]["message"] == "msg 1"

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            list(measure_rate(_entries(1), window_seconds=0))

    def test_empty_input_yields_nothing(self):
        assert list(measure_rate([], window_seconds=5.0)) == []


# ---------------------------------------------------------------------------
# throttle_entries
# ---------------------------------------------------------------------------

class TestThrottleEntries:
    def test_zero_rate_raises(self):
        with pytest.raises(ValueError, match="max_rate"):
            list(throttle_entries(_entries(1), max_rate=0))

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            list(throttle_entries(_entries(1), max_rate=-1.0))

    def test_high_rate_passes_all(self):
        entries = _entries(5)
        result = list(throttle_entries(entries, max_rate=1_000_000))
        assert len(result) == 5

    def test_low_rate_limits_output(self):
        # 1 entry/second — emit many entries instantly, expect only 1 through
        entries = _entries(20)
        result = list(throttle_entries(entries, max_rate=1.0))
        assert len(result) == 1

    def test_empty_input_yields_nothing(self):
        assert list(throttle_entries([], max_rate=10.0)) == []


# ---------------------------------------------------------------------------
# rate_summary
# ---------------------------------------------------------------------------

class TestRateSummary:
    def test_empty_returns_zeros(self):
        result = rate_summary([])
        assert result["count"] == 0
        assert result["duration_seconds"] == 0.0
        assert result["rate_per_second"] == 0.0

    def test_count_matches_input(self):
        entries = _entries(7)
        result = rate_summary(entries)
        assert result["count"] == 7

    def test_no_timestamps_gives_zero_duration(self):
        entries = _entries(4)
        result = rate_summary(entries)
        assert result["duration_seconds"] == 0.0

    def test_with_timestamps_computes_duration(self):
        entries = [
            {"message": "a", "timestamp": "2024-01-01T00:00:00"},
            {"message": "b", "timestamp": "2024-01-01T00:01:00"},
        ]
        result = rate_summary(entries)
        assert result["duration_seconds"] == 60.0
        assert result["rate_per_second"] == pytest.approx(2 / 60, rel=1e-3)

    def test_single_entry_with_timestamp_zero_duration(self):
        entries = [{"message": "only", "timestamp": "2024-06-01T12:00:00"}]
        result = rate_summary(entries)
        assert result["duration_seconds"] == 0.0
