"""Tests for logslice.filters module."""

import pytest
from logslice.filters import filter_by_level, filter_by_pattern, filter_by_fields


DUMMY_ENTRIES = [
    {"timestamp": "2024-01-01T00:00:00", "level": "DEBUG",    "message": "starting up",       "extra": {"service": "api"}},
    {"timestamp": "2024-01-01T00:01:00", "level": "INFO",     "message": "request received",   "extra": {"service": "api"}},
    {"timestamp": "2024-01-01T00:02:00", "level": "WARNING",  "message": "slow response",      "extra": {"service": "worker"}},
    {"timestamp": "2024-01-01T00:03:00", "level": "ERROR",    "message": "connection refused", "extra": {"service": "worker"}},
    {"timestamp": "2024-01-01T00:04:00", "level": "CRITICAL", "message": "disk full",          "extra": {"service": "api"}},
]


class TestFilterByLevel:
    def test_min_level_warning(self):
        result = filter_by_level(DUMMY_ENTRIES, min_level="WARNING")
        levels = [e["level"] for e in result]
        assert levels == ["WARNING", "ERROR", "CRITICAL"]

    def test_min_level_debug_returns_all(self):
        result = filter_by_level(DUMMY_ENTRIES, min_level="DEBUG")
        assert len(result) == len(DUMMY_ENTRIES)

    def test_explicit_levels(self):
        result = filter_by_level(DUMMY_ENTRIES, levels=["INFO", "ERROR"])
        levels = [e["level"] for e in result]
        assert levels == ["INFO", "ERROR"]

    def test_levels_case_insensitive(self):
        result = filter_by_level(DUMMY_ENTRIES, levels=["error", "critical"])
        assert len(result) == 2

    def test_unknown_min_level_raises(self):
        with pytest.raises(ValueError, match="Unknown log level"):
            filter_by_level(DUMMY_ENTRIES, min_level="VERBOSE")

    def test_no_filter_returns_all(self):
        result = filter_by_level(DUMMY_ENTRIES)
        assert result == DUMMY_ENTRIES

    def test_empty_entries(self):
        assert filter_by_level([], min_level="ERROR") == []


class TestFilterByPattern:
    def test_simple_match(self):
        result = filter_by_pattern(DUMMY_ENTRIES, pattern="connection")
        assert len(result) == 1
        assert result[0]["level"] == "ERROR"

    def test_regex_pattern(self):
        result = filter_by_pattern(DUMMY_ENTRIES, pattern=r"slow|disk")
        assert len(result) == 2

    def test_invert(self):
        result = filter_by_pattern(DUMMY_ENTRIES, pattern="starting up", invert=True)
        assert all(e["message"] != "starting up" for e in result)
        assert len(result) == len(DUMMY_ENTRIES) - 1

    def test_no_match_returns_empty(self):
        result = filter_by_pattern(DUMMY_ENTRIES, pattern="nonexistent_xyz")
        assert result == []

    def test_match_on_level_field(self):
        result = filter_by_pattern(DUMMY_ENTRIES, pattern="ERROR", field="level")
        assert len(result) == 1


class TestFilterByFields:
    def test_filter_by_extra_field(self):
        result = filter_by_fields(DUMMY_ENTRIES, service="api")
        assert len(result) == 3

    def test_filter_by_top_level_field(self):
        result = filter_by_fields(DUMMY_ENTRIES, level="DEBUG")
        assert len(result) == 1
        assert result[0]["message"] == "starting up"

    def test_filter_by_multiple_fields(self):
        result = filter_by_fields(DUMMY_ENTRIES, service="worker", level="ERROR")
        assert len(result) == 1
        assert result[0]["message"] == "connection refused"

    def test_no_match_returns_empty(self):
        result = filter_by_fields(DUMMY_ENTRIES, service="database")
        assert result == []

    def test_empty_entries(self):
        assert filter_by_fields([], service="api") == []
