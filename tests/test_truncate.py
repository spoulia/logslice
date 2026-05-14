"""Tests for logslice.truncate."""

from __future__ import annotations

import pytest

from logslice.truncate import (
    truncate_entries,
    truncate_field,
    truncate_fields,
    truncate_message,
    truncate_string,
)


# ---------------------------------------------------------------------------
# truncate_string
# ---------------------------------------------------------------------------

class TestTruncateString:
    def test_short_value_unchanged(self):
        assert truncate_string("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        assert truncate_string("hello", 5) == "hello"

    def test_long_value_is_cut(self):
        result = truncate_string("hello world", 8)
        assert len(result) == 8
        assert result.endswith("...")

    def test_custom_ellipsis(self):
        result = truncate_string("abcdefgh", 5, ellipsis="!")
        assert result == "abcd!"

    def test_max_length_zero_returns_empty(self):
        assert truncate_string("anything", 0) == ""

    def test_max_length_negative_returns_empty(self):
        assert truncate_string("anything", -3) == ""

    def test_ellipsis_longer_than_max_returns_empty_prefix(self):
        # max_length=2, ellipsis="..." -> cut=max(0, 2-3)=0 -> just ellipsis
        result = truncate_string("abcdef", 2)
        assert result == "..."

    def test_empty_string_unchanged(self):
        assert truncate_string("", 10) == ""


# ---------------------------------------------------------------------------
# truncate_field
# ---------------------------------------------------------------------------

class TestTruncateField:
    def test_truncates_target_field(self):
        entry = {"message": "a" * 50, "level": "info"}
        result = truncate_field(entry, "message", 10)
        assert len(result["message"]) == 10
        assert result["level"] == "info"

    def test_missing_field_returns_entry_unchanged(self):
        entry = {"level": "warn"}
        result = truncate_field(entry, "message", 10)
        assert result == entry

    def test_non_string_field_left_alone(self):
        entry = {"count": 99}
        result = truncate_field(entry, "count", 1)
        assert result["count"] == 99

    def test_original_entry_not_mutated(self):
        entry = {"message": "hello world"}
        truncate_field(entry, "message", 5)
        assert entry["message"] == "hello world"


# ---------------------------------------------------------------------------
# truncate_fields
# ---------------------------------------------------------------------------

class TestTruncateFields:
    def test_multiple_fields_truncated(self):
        entry = {"msg": "a" * 20, "src": "b" * 20, "level": "debug"}
        result = truncate_fields(entry, {"msg": 5, "src": 8})
        assert len(result["msg"]) == 5
        assert len(result["src"]) == 8
        assert result["level"] == "debug"

    def test_field_not_in_entry_skipped(self):
        entry = {"level": "info"}
        result = truncate_fields(entry, {"message": 10})
        assert "message" not in result

    def test_original_entry_not_mutated(self):
        entry = {"msg": "a" * 20, "src": "b" * 20}
        truncate_fields(entry, {"msg": 5, "src": 8})
        assert entry["msg"] == "a" * 20
        assert entry["src"] == "b" * 20

    def test_empty_limits_dict_returns_entry_unchanged(self):
        entry = {"message": "hello", "level": "info"}
        result = truncate_fields(entry, {})
        assert result == entry


# --
