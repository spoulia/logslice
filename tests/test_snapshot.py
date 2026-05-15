"""Tests for logslice.snapshot."""

from __future__ import annotations

import json
import os

import pytest

from logslice.snapshot import (
    create_snapshot,
    diff_snapshots,
    load_snapshot,
    restore_entries,
    save_snapshot,
)


def _e(msg: str, level: str = "info") -> dict:
    return {"message": msg, "level": level}


# ---------------------------------------------------------------------------
# create_snapshot
# ---------------------------------------------------------------------------

class TestCreateSnapshot:
    def test_count_matches_input(self):
        entries = [_e("a"), _e("b"), _e("c")]
        snap = create_snapshot(entries)
        assert snap["count"] == 3

    def test_entries_preserved(self):
        entries = [_e("hello")]
        snap = create_snapshot(entries)
        assert snap["entries"][0]["message"] == "hello"

    def test_label_stored(self):
        snap = create_snapshot([], label="my-snap")
        assert snap["label"] == "my-snap"

    def test_default_label_is_empty_string(self):
        snap = create_snapshot([])
        assert snap["label"] == ""

    def test_created_at_present(self):
        snap = create_snapshot([])
        assert "created_at" in snap

    def test_empty_entries(self):
        snap = create_snapshot([])
        assert snap["count"] == 0
        assert snap["entries"] == []


# ---------------------------------------------------------------------------
# save_snapshot / load_snapshot
# ---------------------------------------------------------------------------

class TestSaveLoad:
    def test_round_trip(self, tmp_path):
        entries = [_e("x"), _e("y")]
        snap = create_snapshot(entries, label="rt")
        path = str(tmp_path / "snap.json")
        save_snapshot(snap, path)
        loaded = load_snapshot(path)
        assert loaded["count"] == 2
        assert loaded["label"] == "rt"

    def test_save_returns_absolute_path(self, tmp_path):
        snap = create_snapshot([])
        rel = os.path.join(str(tmp_path), "s.json")
        result = save_snapshot(snap, rel)
        assert os.path.isabs(result)

    def test_load_invalid_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"foo": 1}))
        with pytest.raises(ValueError, match="Invalid snapshot"):
            load_snapshot(str(bad))


# ---------------------------------------------------------------------------
# restore_entries
# ---------------------------------------------------------------------------

class TestRestoreEntries:
    def test_yields_all_entries(self):
        snap = create_snapshot([_e("a"), _e("b")])
        result = list(restore_entries(snap))
        assert len(result) == 2

    def test_empty_snapshot_yields_nothing(self):
        snap = create_snapshot([])
        assert list(restore_entries(snap)) == []


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

class TestDiffSnapshots:
    def test_added_detected(self):
        old = create_snapshot([_e("a")])
        new = create_snapshot([_e("a"), _e("b")])
        d = diff_snapshots(old, new)
        assert len(d["added"]) == 1
        assert d["added"][0]["message"] == "b"

    def test_removed_detected(self):
        old = create_snapshot([_e("a"), _e("b")])
        new = create_snapshot([_e("a")])
        d = diff_snapshots(old, new)
        assert len(d["removed"]) == 1
        assert d["removed"][0]["message"] == "b"

    def test_no_changes(self):
        entries = [_e("a"), _e("b")]
        old = create_snapshot(entries)
        new = create_snapshot(entries)
        d = diff_snapshots(old, new)
        assert d["added"] == []
        assert d["removed"] == []

    def test_custom_key(self):
        old = create_snapshot([{"id": 1, "message": "x"}])
        new = create_snapshot([{"id": 2, "message": "y"}])
        d = diff_snapshots(old, new, key="id")
        assert len(d["added"]) == 1
        assert len(d["removed"]) == 1
