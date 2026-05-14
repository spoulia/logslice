"""Tests for logslice.merge."""

from __future__ import annotations

import json
import os
import tempfile
from typing import List

import pytest

from logslice.merge import merge_sorted, merge_files


def _e(ts: str, msg: str, level: str = "info") -> dict:
    return {"timestamp": ts, "message": msg, "level": level}


# ---------------------------------------------------------------------------
# merge_sorted
# ---------------------------------------------------------------------------

class TestMergeSorted:
    def test_empty_streams_yield_nothing(self):
        result = list(merge_sorted([], []))
        assert result == []

    def test_single_stream_preserved(self):
        entries = [
            _e("2024-01-01T00:00:01Z", "a"),
            _e("2024-01-01T00:00:03Z", "b"),
        ]
        result = list(merge_sorted(entries))
        assert [r["message"] for r in result] == ["a", "b"]

    def test_two_streams_interleaved(self):
        s1 = [_e("2024-01-01T00:00:01Z", "a"), _e("2024-01-01T00:00:05Z", "c")]
        s2 = [_e("2024-01-01T00:00:02Z", "b"), _e("2024-01-01T00:00:06Z", "d")]
        result = list(merge_sorted(s1, s2))
        assert [r["message"] for r in result] == ["a", "b", "c", "d"]

    def test_three_streams(self):
        s1 = [_e("2024-01-01T00:00:01Z", "1")]
        s2 = [_e("2024-01-01T00:00:02Z", "2")]
        s3 = [_e("2024-01-01T00:00:03Z", "3")]
        result = list(merge_sorted(s1, s2, s3))
        assert [r["message"] for r in result] == ["1", "2", "3"]

    def test_entries_without_timestamp_appended_last(self):
        s1 = [_e("2024-01-01T00:00:01Z", "first")]
        s2 = [{"message": "no-ts"}]
        result = list(merge_sorted(s1, s2))
        assert result[-1]["message"] == "no-ts"

    def test_custom_key(self):
        s1 = [{"ts": "2024-01-01T00:00:01Z", "msg": "a"}]
        s2 = [{"ts": "2024-01-01T00:00:00Z", "msg": "b"}]
        result = list(merge_sorted(s1, s2, key="ts"))
        assert result[0]["msg"] == "b"
        assert result[1]["msg"] == "a"

    def test_already_sorted_stream_unchanged(self):
        entries = [
            _e("2024-06-01T10:00:00Z", "x"),
            _e("2024-06-01T11:00:00Z", "y"),
            _e("2024-06-01T12:00:00Z", "z"),
        ]
        result = list(merge_sorted(entries))
        assert [r["message"] for r in result] == ["x", "y", "z"]


# ---------------------------------------------------------------------------
# merge_files
# ---------------------------------------------------------------------------

class TestMergeFiles:
    def _write_ndjson(self, entries: List[dict]) -> str:
        fd, path = tempfile.mkstemp(suffix=".ndjson")
        with os.fdopen(fd, "w") as fh:
            for e in entries:
                fh.write(json.dumps(e) + "\n")
        return path

    def test_merges_two_files(self):
        p1 = self._write_ndjson([
            {"timestamp": "2024-01-01T00:00:01Z", "message": "a"},
            {"timestamp": "2024-01-01T00:00:03Z", "message": "c"},
        ])
        p2 = self._write_ndjson([
            {"timestamp": "2024-01-01T00:00:02Z", "message": "b"},
        ])
        try:
            result = list(merge_files([p1, p2]))
            msgs = [r.get("message") for r in result]
            assert "a" in msgs and "b" in msgs and "c" in msgs
            assert msgs.index("a") < msgs.index("b") < msgs.index("c")
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_empty_file_handled(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        p2 = self._write_ndjson([{"timestamp": "2024-01-01T00:00:01Z", "message": "only"}])
        try:
            result = list(merge_files([path, p2]))
            assert len(result) == 1
        finally:
            os.unlink(path)
            os.unlink(p2)
