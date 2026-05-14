"""Tests for logslice.flatten."""

from __future__ import annotations

import pytest

from logslice.flatten import (
    flatten_entries,
    flatten_entry,
    unflatten_entries,
    unflatten_entry,
)


# ---------------------------------------------------------------------------
# flatten_entry
# ---------------------------------------------------------------------------

class TestFlattenEntry:
    def test_flat_entry_unchanged(self):
        entry = {"level": "info", "message": "hello"}
        assert flatten_entry(entry) == entry

    def test_single_nested_level(self):
        entry = {"a": {"b": 1}}
        assert flatten_entry(entry) == {"a.b": 1}

    def test_double_nested(self):
        entry = {"a": {"b": {"c": 42}}}
        assert flatten_entry(entry) == {"a.b.c": 42}

    def test_mixed_flat_and_nested(self):
        entry = {"level": "error", "meta": {"host": "srv1", "pid": 99}}
        result = flatten_entry(entry)
        assert result == {"level": "error", "meta.host": "srv1", "meta.pid": 99}

    def test_custom_separator(self):
        entry = {"a": {"b": 1}}
        assert flatten_entry(entry, sep="/") == {"a/b": 1}

    def test_empty_entry(self):
        assert flatten_entry({}) == {}

    def test_list_value_preserved(self):
        entry = {"tags": ["web", "api"]}
        assert flatten_entry(entry) == {"tags": ["web", "api"]}


# ---------------------------------------------------------------------------
# unflatten_entry
# ---------------------------------------------------------------------------

class TestUnflattenEntry:
    def test_simple_key_unchanged(self):
        entry = {"level": "info"}
        assert unflatten_entry(entry) == entry

    def test_single_dot_key(self):
        assert unflatten_entry({"a.b": 1}) == {"a": {"b": 1}}

    def test_double_dot_key(self):
        assert unflatten_entry({"a.b.c": 42}) == {"a": {"b": {"c": 42}}}

    def test_sibling_keys_merged(self):
        entry = {"meta.host": "srv1", "meta.pid": 99}
        assert unflatten_entry(entry) == {"meta": {"host": "srv1", "pid": 99}}

    def test_custom_separator(self):
        assert unflatten_entry({"a/b": 1}, sep="/") == {"a": {"b": 1}}

    def test_empty_entry(self):
        assert unflatten_entry({}) == {}


# ---------------------------------------------------------------------------
# round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_flatten_then_unflatten(self):
        original = {"level": "warn", "meta": {"host": "srv", "region": "us-east"}}
        assert unflatten_entry(flatten_entry(original)) == original

    def test_unflatten_then_flatten(self):
        flat = {"level": "info", "meta.host": "srv", "meta.pid": 1}
        assert flatten_entry(unflatten_entry(flat)) == flat


# ---------------------------------------------------------------------------
# bulk helpers
# ---------------------------------------------------------------------------

def test_flatten_entries_applies_to_all():
    entries = [{"a": {"b": 1}}, {"x": {"y": 2}}]
    result = flatten_entries(entries)
    assert result == [{"a.b": 1}, {"x.y": 2}]


def test_unflatten_entries_applies_to_all():
    entries = [{"a.b": 1}, {"x.y": 2}]
    result = unflatten_entries(entries)
    assert result == [{"a": {"b": 1}}, {"x": {"y": 2}}]


def test_flatten_entries_empty_list():
    assert flatten_entries([]) == []
