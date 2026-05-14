"""Tests for logslice.normalize."""

from __future__ import annotations

import pytest

from logslice.normalize import (
    get_normalizer,
    normalize_entries,
    normalize_field,
    normalize_fields,
    normalize_level,
)


def _e(**kwargs):
    base = {"message": "hello", "level": "info"}
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# get_normalizer
# ---------------------------------------------------------------------------

class TestGetNormalizer:
    def test_lower_exists(self):
        assert get_normalizer("lower") is not None

    def test_upper_exists(self):
        assert get_normalizer("upper") is not None

    def test_unknown_returns_none(self):
        assert get_normalizer("nonexistent") is None

    def test_lower_transforms(self):
        fn = get_normalizer("lower")
        assert fn("HELLO") == "hello"

    def test_upper_transforms(self):
        fn = get_normalizer("upper")
        assert fn("hello") == "HELLO"

    def test_strip_removes_whitespace(self):
        fn = get_normalizer("strip")
        assert fn("  hi  ") == "hi"

    def test_int_converts(self):
        fn = get_normalizer("int")
        assert fn("42") == 42

    def test_bool_true_variants(self):
        fn = get_normalizer("bool")
        for v in ("1", "true", "True", "yes"):
            assert fn(v) is True

    def test_bool_false_variant(self):
        fn = get_normalizer("bool")
        assert fn("false") is False


# ---------------------------------------------------------------------------
# normalize_field
# ---------------------------------------------------------------------------

class TestNormalizeField:
    def test_applies_normalizer_to_field(self):
        entry = _e(level="info")
        result = normalize_field(entry, "level", "upper")
        assert result["level"] == "INFO"

    def test_missing_field_is_ignored(self):
        entry = _e()
        result = normalize_field(entry, "nonexistent", "upper")
        assert result == entry

    def test_does_not_mutate_original(self):
        entry = _e(level="info")
        normalize_field(entry, "level", "upper")
        assert entry["level"] == "info"

    def test_unknown_normalizer_raises(self):
        with pytest.raises(ValueError, match="Unknown normalizer"):
            normalize_field(_e(), "level", "bogus")


# ---------------------------------------------------------------------------
# normalize_fields
# ---------------------------------------------------------------------------

class TestNormalizeFields:
    def test_applies_multiple_normalizers(self):
        entry = {"level": "info", "message": "  hello  ", "count": "7"}
        result = normalize_fields(entry, {"level": "upper", "message": "strip", "count": "int"})
        assert result == {"level": "INFO", "message": "hello", "count": 7}

    def test_unknown_normalizer_raises(self):
        with pytest.raises(ValueError):
            normalize_fields(_e(), {"level": "bad"})


# ---------------------------------------------------------------------------
# normalize_entries
# ---------------------------------------------------------------------------

class TestNormalizeEntries:
    def test_processes_all_entries(self):
        entries = [_e(level="info"), _e(level="warn"), _e(level="error")]
        result = normalize_entries(entries, {"level": "upper"})
        assert [e["level"] for e in result] == ["INFO", "WARN", "ERROR"]

    def test_empty_list_returns_empty(self):
        assert normalize_entries([], {"level": "upper"}) == []


# ---------------------------------------------------------------------------
# normalize_level convenience
# ---------------------------------------------------------------------------

class TestNormalizeLevel:
    def test_uppercases_level(self):
        entry = _e(level="debug")
        assert normalize_level(entry)["level"] == "DEBUG"

    def test_custom_field(self):
        entry = {"severity": "critical", "message": "x"}
        result = normalize_level(entry, field="severity")
        assert result["severity"] == "CRITICAL"
