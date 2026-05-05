"""Tests for logslice.dedup."""

import pytest
from logslice.dedup import _entry_key, dedup_entries


def _entry(message: str, level: str = "INFO", **extra) -> dict:
    return {"message": message, "level": level, **extra}


class TestEntryKey:
    def test_same_message_and_level_equal(self):
        a = _entry_key(_entry("hello", "INFO"))
        b = _entry_key(_entry("hello", "INFO"))
        assert a == b

    def test_different_message_differ(self):
        a = _entry_key(_entry("hello"))
        b = _entry_key(_entry("world"))
        assert a != b

    def test_different_level_differ(self):
        a = _entry_key(_entry("hello", "INFO"))
        b = _entry_key(_entry("hello", "ERROR"))
        assert a != b

    def test_custom_fields(self):
        e = {"message": "x", "level": "INFO", "source": "app"}
        k1 = _entry_key(e, fields=["source"])
        k2 = _entry_key({"message": "y", "level": "DEBUG", "source": "app"}, fields=["source"])
        assert k1 == k2

    def test_missing_field_treated_as_empty(self):
        k1 = _entry_key({}, fields=["nonexistent"])
        k2 = _entry_key({"nonexistent": ""}, fields=["nonexistent"])
        assert k1 == k2


class TestDedupEntries:
    def test_empty_input(self):
        assert list(dedup_entries([])) == []

    def test_no_duplicates_unchanged(self):
        entries = [_entry("a"), _entry("b"), _entry("c")]
        result = list(dedup_entries(entries))
        assert result == entries

    def test_keep_first_removes_later_dupes(self):
        e1 = _entry("dup", extra="first")
        e2 = _entry("dup", extra="second")
        result = list(dedup_entries([e1, e2], keep="first"))
        assert result == [e1]

    def test_keep_last_removes_earlier_dupes(self):
        e1 = _entry("dup", extra="first")
        e2 = _entry("dup", extra="second")
        result = list(dedup_entries([e1, e2], keep="last"))
        assert result == [e2]

    def test_order_preserved_keep_first(self):
        entries = [_entry("a"), _entry("b"), _entry("a"), _entry("c")]
        result = list(dedup_entries(entries, keep="first"))
        messages = [e["message"] for e in result]
        assert messages == ["a", "b", "c"]

    def test_order_preserved_keep_last(self):
        entries = [_entry("a"), _entry("b"), _entry("a"), _entry("c")]
        result = list(dedup_entries(entries, keep="last"))
        messages = [e["message"] for e in result]
        assert messages == ["b", "a", "c"]

    def test_custom_fields_dedup(self):
        e1 = {"message": "x", "level": "INFO", "source": "svc"}
        e2 = {"message": "y", "level": "ERROR", "source": "svc"}
        result = list(dedup_entries([e1, e2], fields=["source"]))
        assert result == [e1]

    def test_invalid_keep_raises(self):
        with pytest.raises(ValueError, match="keep must be"):
            list(dedup_entries([_entry("x")], keep="middle"))
