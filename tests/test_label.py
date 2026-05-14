"""Tests for logslice.label."""

from __future__ import annotations

import pytest

from logslice.label import (
    clear_labels,
    filter_by_label,
    label_by_field,
    label_by_pattern,
)


def _e(message: str = "hello", **kwargs) -> dict:
    return {"message": message, **kwargs}


# ---------------------------------------------------------------------------
# label_by_pattern
# ---------------------------------------------------------------------------

class TestLabelByPattern:
    def test_matching_entry_gets_label(self):
        entries = [_e("ERROR: disk full")]
        result = label_by_pattern(entries, r"ERROR", "error")
        assert result[0]["label"] == "error"

    def test_non_matching_entry_unchanged(self):
        entries = [_e("all good")]
        result = label_by_pattern(entries, r"ERROR", "error")
        assert "label" not in result[0]

    def test_custom_field(self):
        entries = [{"message": "ok", "source": "db.log"}]
        result = label_by_pattern(entries, r"db", "database", field="source")
        assert result[0]["label"] == "database"

    def test_custom_label_key(self):
        entries = [_e("ERROR")]
        result = label_by_pattern(entries, r"ERROR", "err", label_key="tag")
        assert result[0]["tag"] == "err"

    def test_second_label_appended_to_list(self):
        entries = [_e("ERROR timeout", label="slow")]
        result = label_by_pattern(entries, r"ERROR", "error")
        assert "error" in result[0]["label"]
        assert "slow" in result[0]["label"]

    def test_duplicate_label_not_added_twice(self):
        entries = [_e("ERROR", label="error")]
        result = label_by_pattern(entries, r"ERROR", "error")
        lbl = result[0]["label"]
        count = lbl.count("error") if isinstance(lbl, list) else 1
        assert count == 1

    def test_original_entries_not_mutated(self):
        original = [_e("ERROR")]
        label_by_pattern(original, r"ERROR", "error")
        assert "label" not in original[0]


# ---------------------------------------------------------------------------
# label_by_field
# ---------------------------------------------------------------------------

class TestLabelByField:
    def test_matching_field_value_gets_label(self):
        entries = [{"message": "x", "level": "error"}]
        result = label_by_field(entries, {"level=error": "critical"})
        assert result[0]["label"] == "critical"

    def test_non_matching_value_unchanged(self):
        entries = [{"message": "x", "level": "info"}]
        result = label_by_field(entries, {"level=error": "critical"})
        assert "label" not in result[0]

    def test_multiple_mappings_applied(self):
        entries = [{"message": "x", "level": "error", "env": "prod"}]
        result = label_by_field(
            entries,
            {"level=error": "err", "env=prod": "production"},
        )
        labels = result[0]["label"]
        assert "err" in labels
        assert "production" in labels


# ---------------------------------------------------------------------------
# clear_labels
# ---------------------------------------------------------------------------

class TestClearLabels:
    def test_removes_label_key(self):
        entries = [{"message": "hi", "label": "tagged"}]
        result = clear_labels(entries)
        assert "label" not in result[0]

    def test_other_fields_preserved(self):
        entries = [{"message": "hi", "label": "tagged", "level": "info"}]
        result = clear_labels(entries)
        assert result[0]["level"] == "info"

    def test_custom_label_key(self):
        entries = [{"message": "hi", "tag": "x"}]
        result = clear_labels(entries, label_key="tag")
        assert "tag" not in result[0]


# ---------------------------------------------------------------------------
# filter_by_label
# ---------------------------------------------------------------------------

class TestFilterByLabel:
    def test_returns_matching_string_label(self):
        entries = [_e(label="error"), _e(label="info")]
        result = filter_by_label(entries, "error")
        assert len(result) == 1
        assert result[0]["label"] == "error"

    def test_returns_matching_list_label(self):
        entries = [_e(label=["error", "slow"]), _e(label="info")]
        result = filter_by_label(entries, "slow")
        assert len(result) == 1

    def test_no_label_field_excluded(self):
        entries = [_e()]
        result = filter_by_label(entries, "error")
        assert result == []
