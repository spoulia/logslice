"""Tests for logslice.annotate."""

from __future__ import annotations

import pytest

from logslice.annotate import (
    annotate_entry,
    annotate_entries,
    annotate_by_pattern,
    annotate_by_level,
)


def _e(**kwargs):
    base = {"message": "hello", "level": "info"}
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# annotate_entry
# ---------------------------------------------------------------------------

class TestAnnotateEntry:
    def test_adds_new_key(self):
        result = annotate_entry(_e(), {"env": "prod"})
        assert result["env"] == "prod"

    def test_original_keys_preserved(self):
        result = annotate_entry(_e(message="hi"), {"env": "prod"})
        assert result["message"] == "hi"

    def test_existing_key_not_overwritten_by_default(self):
        result = annotate_entry(_e(level="error"), {"level": "debug"})
        assert result["level"] == "error"

    def test_existing_key_overwritten_when_flag_set(self):
        result = annotate_entry(_e(level="error"), {"level": "debug"}, overwrite=True)
        assert result["level"] == "debug"

    def test_returns_copy_not_same_object(self):
        entry = _e()
        result = annotate_entry(entry, {"env": "prod"})
        assert result is not entry

    def test_empty_annotations_returns_equivalent(self):
        entry = _e(message="x")
        result = annotate_entry(entry, {})
        assert result == entry


# ---------------------------------------------------------------------------
# annotate_entries
# ---------------------------------------------------------------------------

class TestAnnotateEntries:
    def test_all_entries_get_annotation(self):
        entries = [_e(), _e(message="bye")]
        results = list(annotate_entries(entries, {"region": "eu"}))
        assert all(r["region"] == "eu" for r in results)

    def test_empty_input_yields_nothing(self):
        assert list(annotate_entries([], {"x": 1})) == []

    def test_returns_iterator(self):
        import types
        result = annotate_entries([_e()], {"k": "v"})
        assert isinstance(result, types.GeneratorType)


# ---------------------------------------------------------------------------
# annotate_by_pattern
# ---------------------------------------------------------------------------

class TestAnnotateByPattern:
    def test_matching_entry_is_annotated(self):
        entries = [_e(message="error occurred")]
        results = list(annotate_by_pattern(entries, r"error", {"flag": True}))
        assert results[0]["flag"] is True

    def test_non_matching_entry_unchanged(self):
        entries = [_e(message="all good")]
        results = list(annotate_by_pattern(entries, r"error", {"flag": True}))
        assert "flag" not in results[0]

    def test_custom_field_used(self):
        entries = [{"level": "warn", "source": "db"}]
        results = list(
            annotate_by_pattern(entries, r"db", {"team": "dba"}, field="source")
        )
        assert results[0]["team"] == "dba"


# ---------------------------------------------------------------------------
# annotate_by_level
# ---------------------------------------------------------------------------

class TestAnnotateByLevel:
    def test_error_entry_gets_annotation(self):
        entries = [_e(level="error")]
        results = list(annotate_by_level(entries, {"error": {"alert": True}}))
        assert results[0]["alert"] is True

    def test_non_matching_level_unchanged(self):
        entries = [_e(level="info")]
        results = list(annotate_by_level(entries, {"error": {"alert": True}}))
        assert "alert" not in results[0]

    def test_case_insensitive_level_match(self):
        entries = [_e(level="ERROR")]
        results = list(annotate_by_level(entries, {"error": {"prio": "high"}}))
        assert results[0]["prio"] == "high"

    def test_multiple_levels_annotated_correctly(self):
        entries = [_e(level="warn"), _e(level="info")]
        mapping = {"warn": {"tag": "warning"}, "info": {"tag": "ok"}}
        results = list(annotate_by_level(entries, mapping))
        assert results[0]["tag"] == "warning"
        assert results[1]["tag"] == "ok"
