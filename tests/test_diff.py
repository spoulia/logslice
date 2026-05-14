"""Tests for logslice.diff."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from logslice.diff import (
    _entry_signature,
    diff_entries,
    diff_summary,
    format_diff_text,
)


def _e(message: str, level: str = "INFO", **kwargs: Any) -> Dict[str, Any]:
    return {"message": message, "level": level, **kwargs}


# ---------------------------------------------------------------------------
# _entry_signature
# ---------------------------------------------------------------------------

class TestEntrySignature:
    def test_returns_tuple_of_field_values(self):
        e = _e("hello", "DEBUG")
        assert _entry_signature(e, ["message", "level"]) == ("hello", "DEBUG")

    def test_missing_field_is_none(self):
        e = _e("hello")
        assert _entry_signature(e, ["message", "source"]) == ("hello", None)

    def test_single_field(self):
        e = _e("only message")
        assert _entry_signature(e, ["message"]) == ("only message",)


# ---------------------------------------------------------------------------
# diff_entries
# ---------------------------------------------------------------------------

class TestDiffEntries:
    def test_identical_lists_have_no_added_or_removed(self):
        entries = [_e("a"), _e("b")]
        result = diff_entries(entries, entries)
        assert result["added"] == []
        assert result["removed"] == []
        assert len(result["common"]) == 2

    def test_new_entry_appears_in_added(self):
        left = [_e("a")]
        right = [_e("a"), _e("b")]
        result = diff_entries(left, right)
        assert len(result["added"]) == 1
        assert result["added"][0]["message"] == "b"

    def test_missing_entry_appears_in_removed(self):
        left = [_e("a"), _e("b")]
        right = [_e("a")]
        result = diff_entries(left, right)
        assert len(result["removed"]) == 1
        assert result["removed"][0]["message"] == "b"

    def test_custom_fields(self):
        left = [_e("msg", "INFO", source="svc-a")]
        right = [_e("msg", "INFO", source="svc-b")]
        result = diff_entries(left, right, fields=["source"])
        assert len(result["added"]) == 1
        assert len(result["removed"]) == 1

    def test_empty_inputs(self):
        result = diff_entries([], [])
        assert result == {"added": [], "removed": [], "common": []}

    def test_duplicate_signatures_last_wins(self):
        # dict comprehension keeps last seen; both sides identical
        left = [_e("dup"), _e("dup")]
        right = [_e("dup")]
        result = diff_entries(left, right)
        assert result["added"] == []
        assert result["removed"] == []


# ---------------------------------------------------------------------------
# diff_summary
# ---------------------------------------------------------------------------

class TestDiffSummary:
    def test_counts_match_lists(self):
        result = {"added": [_e("x")], "removed": [], "common": [_e("y"), _e("z")]}
        s = diff_summary(result)
        assert s == {"added": 1, "removed": 0, "common": 2}

    def test_empty_result(self):
        s = diff_summary({"added": [], "removed": [], "common": []})
        assert s["added"] == 0


# ---------------------------------------------------------------------------
# format_diff_text
# ---------------------------------------------------------------------------

class TestFormatDiffText:
    def test_added_lines_prefixed_with_plus(self):
        result = {"added": [_e("new msg")], "removed": [], "common": []}
        text = format_diff_text(result)
        assert "+ new msg" in text

    def test_removed_lines_prefixed_with_minus(self):
        result = {"added": [], "removed": [_e("old msg")], "common": []}
        text = format_diff_text(result)
        assert "- old msg" in text

    def test_no_diff_message_when_empty(self):
        result = {"added": [], "removed": [], "common": []}
        text = format_diff_text(result)
        assert "no differences" in text

    def test_summary_line_included(self):
        result = {"added": [_e("x")], "removed": [], "common": [_e("y")]}
        text = format_diff_text(result)
        assert "added=1" in text
        assert "common=1" in text
