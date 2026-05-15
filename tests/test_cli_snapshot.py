"""Tests for logslice.cli_snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from io import StringIO
from unittest import mock

import pytest

from logslice.cli_snapshot import add_snapshot_subparser, run_snapshot
from logslice.snapshot import create_snapshot, save_snapshot


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    add_snapshot_subparser(sub)
    return p


class TestAddSnapshotSubparser:
    def test_subparser_registered(self):
        p = _parser()
        args = p.parse_args(["snapshot", "create", "out.json"])
        assert args.command == "snapshot"

    def test_create_output_argument(self):
        p = _parser()
        args = p.parse_args(["snapshot", "create", "out.json"])
        assert args.output == "out.json"

    def test_create_label_default(self):
        p = _parser()
        args = p.parse_args(["snapshot", "create", "out.json"])
        assert args.label == ""

    def test_restore_input_argument(self):
        p = _parser()
        args = p.parse_args(["snapshot", "restore", "snap.json"])
        assert args.input == "snap.json"

    def test_diff_key_default(self):
        p = _parser()
        args = p.parse_args(["snapshot", "diff", "a.json", "b.json"])
        assert args.key == "message"


class TestRunSnapshotCreate:
    def test_create_writes_file(self, tmp_path):
        out = str(tmp_path / "snap.json")
        stdin_data = json.dumps({"message": "hello"}) + "\n"
        p = _parser()
        args = p.parse_args(["snapshot", "create", out, "--label", "test"])
        with mock.patch("sys.stdin", StringIO(stdin_data)):
            run_snapshot(args)
        with open(out) as fh:
            data = json.load(fh)
        assert data["count"] == 1
        assert data["label"] == "test"


class TestRunSnapshotRestore:
    def test_restore_prints_entries(self, tmp_path, capsys):
        snap = create_snapshot([{"message": "restored"}])
        path = str(tmp_path / "snap.json")
        save_snapshot(snap, path)
        p = _parser()
        args = p.parse_args(["snapshot", "restore", path])
        run_snapshot(args)
        captured = capsys.readouterr()
        assert "restored" in captured.out


class TestRunSnapshotDiff:
    def test_diff_shows_added(self, tmp_path, capsys):
        old_snap = create_snapshot([{"message": "a"}])
        new_snap = create_snapshot([{"message": "a"}, {"message": "b"}])
        old_path = str(tmp_path / "old.json")
        new_path = str(tmp_path / "new.json")
        save_snapshot(old_snap, old_path)
        save_snapshot(new_snap, new_path)
        p = _parser()
        args = p.parse_args(["snapshot", "diff", old_path, new_path])
        run_snapshot(args)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert len(result["added"]) == 1
        assert result["added"][0]["message"] == "b"
