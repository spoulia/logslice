"""Tests for logslice.index."""

from __future__ import annotations

import pytest

from logslice.index import Index, build_index


def _e(level="info", source="app", message="hello", **kw) -> dict:
    return {"level": level, "source": source, "message": message, **kw}


# ---------------------------------------------------------------------------
class TestIndexAdd:
    def test_len_increases(self):
        idx = Index()
        idx.add(_e())
        assert len(idx) == 1

    def test_add_returns_position(self):
        idx = Index()
        assert idx.add(_e()) == 0
        assert idx.add(_e()) == 1

    def test_add_many(self):
        idx = Index()
        idx.add_many([_e(), _e(), _e()])
        assert len(idx) == 3

    def test_iter_yields_all(self):
        entries = [_e(message="a"), _e(message="b")]
        idx = build_index(entries)
        assert list(idx) == entries


# ---------------------------------------------------------------------------
class TestIndexLookup:
    def test_lookup_by_level(self):
        idx = build_index([_e(level="error"), _e(level="info"), _e(level="error")])
        result = idx.lookup("level", "error")
        assert len(result) == 2
        assert all(e["level"] == "error" for e in result)

    def test_lookup_missing_value_returns_empty(self):
        idx = build_index([_e(level="info")])
        assert idx.lookup("level", "critical") == []

    def test_lookup_unindexed_field_returns_empty(self):
        idx = build_index([_e()], fields=["level"])
        assert idx.lookup("source", "app") == []

    def test_lookup_many(self):
        entries = [
            _e(level="error"),
            _e(level="warning"),
            _e(level="info"),
        ]
        idx = build_index(entries)
        result = idx.lookup_many("level", ["error", "warning"])
        assert len(result) == 2

    def test_lookup_many_no_duplicates(self):
        idx = build_index([_e(level="error")])
        result = idx.lookup_many("level", ["error", "error"])
        assert len(result) == 1


# ---------------------------------------------------------------------------
class TestIndexAllValues:
    def test_returns_distinct_values(self):
        idx = build_index([
            _e(level="info"),
            _e(level="error"),
            _e(level="info"),
        ])
        vals = idx.all_values("level")
        assert set(vals) == {"info", "error"}

    def test_unknown_field_returns_empty(self):
        idx = build_index([_e()], fields=["level"])
        assert idx.all_values("source") == []


# ---------------------------------------------------------------------------
class TestIndexClear:
    def test_clear_resets_len(self):
        idx = build_index([_e(), _e()])
        idx.clear()
        assert len(idx) == 0

    def test_clear_removes_lookup_results(self):
        idx = build_index([_e(level="error")])
        idx.clear()
        assert idx.lookup("level", "error") == []

    def test_can_add_after_clear(self):
        idx = build_index([_e()])
        idx.clear()
        idx.add(_e(level="debug"))
        assert len(idx) == 1
        assert idx.lookup("level", "debug") != []


# ---------------------------------------------------------------------------
class TestBuildIndex:
    def test_custom_fields(self):
        idx = build_index([_e()], fields=["message"])
        assert idx.all_values("message") == ["hello"]

    def test_none_field_value_not_indexed(self):
        idx = build_index([{"level": None, "source": "app"}])
        assert idx.lookup("level", None) == []
