"""Tests for logslice.rotate."""

from __future__ import annotations

import os
import pytest

from logslice.rotate import (
    detect_rotation,
    read_new_lines,
    iter_with_rotation,
    _file_inode,
    _file_size,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path, content):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# _file_inode / _file_size
# ---------------------------------------------------------------------------

def test_file_inode_returns_none_for_missing_file(tmp_path):
    assert _file_inode(str(tmp_path / "ghost.log")) is None


def test_file_size_returns_zero_for_missing_file(tmp_path):
    assert _file_size(str(tmp_path / "ghost.log")) == 0


def test_file_size_matches_content(tmp_path):
    p = tmp_path / "a.log"
    _write(str(p), "hello")
    assert _file_size(str(p)) == 5


# ---------------------------------------------------------------------------
# detect_rotation
# ---------------------------------------------------------------------------

def test_no_rotation_when_inode_and_size_unchanged(tmp_path):
    p = tmp_path / "app.log"
    _write(str(p), "line1\n")
    inode = _file_inode(str(p))
    size = _file_size(str(p))
    assert detect_rotation(str(p), inode, size) is False


def test_rotation_detected_on_truncation(tmp_path):
    p = tmp_path / "app.log"
    _write(str(p), "line1\nline2\n")
    size = _file_size(str(p))
    inode = _file_inode(str(p))
    # truncate
    _write(str(p), "")
    assert detect_rotation(str(p), inode, size) is True


def test_rotation_detected_on_inode_change(tmp_path):
    p = tmp_path / "app.log"
    _write(str(p), "old\n")
    old_inode = _file_inode(str(p))
    size = _file_size(str(p))
    # simulate rotation: remove and recreate
    os.remove(str(p))
    _write(str(p), "new\n")
    assert detect_rotation(str(p), old_inode, size) is True


def test_no_rotation_when_file_missing(tmp_path):
    """If the file doesn't exist yet, detect_rotation returns False (not an error)."""
    result = detect_rotation(str(tmp_path / "missing.log"), None, 0)
    assert result is False


# ---------------------------------------------------------------------------
# read_new_lines
# ---------------------------------------------------------------------------

def test_read_new_lines_from_start(tmp_path):
    p = tmp_path / "app.log"
    _write(str(p), "alpha\nbeta\ngamma\n")
    lines, pos = read_new_lines(str(p), 0)
    assert lines == ["alpha", "beta", "gamma"]
    assert pos > 0


def test_read_new_lines_from_offset(tmp_path):
    p = tmp_path / "app.log"
    _write(str(p), "alpha\nbeta\n")
    _, pos = read_new_lines(str(p), 0)
    # append
    with open(str(p), "a") as fh:
        fh.write("gamma\n")
    lines, new_pos = read_new_lines(str(p), pos)
    assert lines == ["gamma"]
    assert new_pos > pos


def test_read_new_lines_restarts_on_truncation(tmp_path):
    p = tmp_path / "app.log"
    _write(str(p), "alpha\nbeta\n")
    _, pos = read_new_lines(str(p), 0)
    _write(str(p), "new\n")
    lines, _ = read_new_lines(str(p), pos)  # pos > current size → restart
    assert lines == ["new"]


def test_read_new_lines_missing_file(tmp_path):
    lines, pos = read_new_lines(str(tmp_path / "ghost.log"), 42)
    assert lines == []
    assert pos == 42


# ---------------------------------------------------------------------------
# iter_with_rotation
# ---------------------------------------------------------------------------

def test_iter_with_rotation_yields_all_lines(tmp_path):
    p = tmp_path / "app.log"
    _write(str(p), "one\ntwo\nthree\n")
    results = list(iter_with_rotation(str(p), start_position=0))
    assert [r[0] for r in results] == ["one", "two", "three"]


def test_iter_with_rotation_position_advances(tmp_path):
    p = tmp_path / "app.log"
    _write(str(p), "x\ny\n")
    positions = [pos for _, pos in iter_with_rotation(str(p), 0)]
    # All positions should be the same (end-of-file after reading all lines)
    assert all(pos > 0 for pos in positions)
