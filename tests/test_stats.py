"""Tests for logslice.stats module."""

import pytest
from logslice.stats import compute_stats, format_stats_text


SAMPLE_ENTRIES = [
    {"timestamp": "2024-01-01T10:00:00", "level": "INFO", "source": "app", "message": "started"},
    {"timestamp": "2024-01-01T10:01:00", "level": "DEBUG", "source": "app", "message": "debug msg"},
    {"timestamp": "2024-01-01T10:02:00", "level": "ERROR", "source": "db", "message": "conn failed"},
    {"timestamp": "2024-01-01T10:03:00", "level": "WARNING", "source": "app", "message": "slow query"},
    {"timestamp": "2024-01-01T10:04:00", "level": "CRITICAL", "source": "db", "message": "crash"},
]


class TestComputeStats:
    def test_empty_entries(self):
        stats = compute_stats([])
        assert stats["total"] == 0
        assert stats["by_level"] == {}
        assert stats["first_timestamp"] is None
        assert stats["error_rate"] == 0.0

    def test_total_count(self):
        stats = compute_stats(SAMPLE_ENTRIES)
        assert stats["total"] == 5

    def test_level_counts(self):
        stats = compute_stats(SAMPLE_ENTRIES)
        assert stats["by_level"]["INFO"] == 1
        assert stats["by_level"]["ERROR"] == 1
        assert stats["by_level"]["CRITICAL"] == 1

    def test_source_counts(self):
        stats = compute_stats(SAMPLE_ENTRIES)
        assert stats["by_source"]["app"] == 3
        assert stats["by_source"]["db"] == 2

    def test_timestamps(self):
        stats = compute_stats(SAMPLE_ENTRIES)
        assert stats["first_timestamp"] == "2024-01-01T10:00:00"
        assert stats["last_timestamp"] == "2024-01-01T10:04:00"

    def test_error_rate(self):
        stats = compute_stats(SAMPLE_ENTRIES)
        # ERROR + CRITICAL = 2 out of 5
        assert stats["error_rate"] == pytest.approx(0.4, abs=1e-4)

    def test_missing_level_defaults_to_unknown(self):
        entries = [{"message": "no level here"}]
        stats = compute_stats(entries)
        assert "UNKNOWN" in stats["by_level"]

    def test_level_case_normalised(self):
        entries = [{"level": "error"}, {"level": "ERROR"}]
        stats = compute_stats(entries)
        assert stats["by_level"].get("ERROR") == 2


class TestFormatStatsText:
    def test_contains_total(self):
        stats = compute_stats(SAMPLE_ENTRIES)
        text = format_stats_text(stats)
        assert "5" in text

    def test_contains_error_rate(self):
        stats = compute_stats(SAMPLE_ENTRIES)
        text = format_stats_text(stats)
        assert "40.00%" in text

    def test_contains_level_names(self):
        stats = compute_stats(SAMPLE_ENTRIES)
        text = format_stats_text(stats)
        assert "ERROR" in text
        assert "INFO" in text

    def test_empty_stats_no_crash(self):
        stats = compute_stats([])
        text = format_stats_text(stats)
        assert "0" in text
