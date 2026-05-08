"""Tests for logslice.checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logslice.checkpoint import (
    clear_checkpoint,
    get_position,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture()
def cp_dir(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints"


class TestSaveCheckpoint:
    def test_creates_file(self, cp_dir: Path) -> None:
        path = save_checkpoint("mylog.log", 42, directory=cp_dir)
        assert path.exists()

    def test_returns_path_inside_directory(self, cp_dir: Path) -> None:
        path = save_checkpoint("app.log", 0, directory=cp_dir)
        assert path.parent == cp_dir

    def test_payload_contains_position(self, cp_dir: Path) -> None:
        save_checkpoint("app.log", 1024, directory=cp_dir)
        cp = load_checkpoint("app.log", directory=cp_dir)
        assert cp is not None
        assert cp["position"] == 1024

    def test_payload_contains_name(self, cp_dir: Path) -> None:
        save_checkpoint("app.log", 0, directory=cp_dir)
        cp = load_checkpoint("app.log", directory=cp_dir)
        assert cp["name"] == "app.log"

    def test_extra_fields_stored(self, cp_dir: Path) -> None:
        save_checkpoint("app.log", 0, directory=cp_dir, extra={"host": "srv1"})
        cp = load_checkpoint("app.log", directory=cp_dir)
        assert cp is not None
        assert cp["extra"]["host"] == "srv1"

    def test_overwrite_updates_position(self, cp_dir: Path) -> None:
        save_checkpoint("app.log", 100, directory=cp_dir)
        save_checkpoint("app.log", 999, directory=cp_dir)
        assert get_position("app.log", directory=cp_dir) == 999

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        deep = tmp_path / "a" / "b" / "c"
        save_checkpoint("x.log", 5, directory=deep)
        assert deep.exists()


class TestLoadCheckpoint:
    def test_missing_returns_none(self, cp_dir: Path) -> None:
        result = load_checkpoint("nonexistent.log", directory=cp_dir)
        assert result is None

    def test_returns_dict(self, cp_dir: Path) -> None:
        save_checkpoint("x.log", 7, directory=cp_dir)
        result = load_checkpoint("x.log", directory=cp_dir)
        assert isinstance(result, dict)


class TestClearCheckpoint:
    def test_returns_true_when_existed(self, cp_dir: Path) -> None:
        save_checkpoint("z.log", 0, directory=cp_dir)
        assert clear_checkpoint("z.log", directory=cp_dir) is True

    def test_returns_false_when_missing(self, cp_dir: Path) -> None:
        assert clear_checkpoint("ghost.log", directory=cp_dir) is False

    def test_file_deleted(self, cp_dir: Path) -> None:
        path = save_checkpoint("z.log", 0, directory=cp_dir)
        clear_checkpoint("z.log", directory=cp_dir)
        assert not path.exists()


class TestGetPosition:
    def test_no_checkpoint_returns_zero(self, cp_dir: Path) -> None:
        assert get_position("missing.log", directory=cp_dir) == 0

    def test_returns_saved_position(self, cp_dir: Path) -> None:
        save_checkpoint("f.log", 512, directory=cp_dir)
        assert get_position("f.log", directory=cp_dir) == 512
