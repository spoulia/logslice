"""Tests for logslice.cli_diff."""

from __future__ import annotations

import argparse
import json
import os
import textwrap
from io import StringIO
from unittest.mock import patch

import pytest

from logslice.cli_diff import add_diff_subparser, run_diff


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "left": "left.log",
        "right": "right.log",
        "fields": ["message", "level"],
        "fmt": "text",
        "show": "all",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddDiffSubparser:
    def _parser(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers(dest="cmd")
        add_diff_subparser(sub)
        return p

    def test_subparser_registered(self):
        p = self._parser()
        args = p.parse_args(["diff", "a.log", "b.log"])
        assert args.cmd == "diff"

    def test_default_fields(self):
        p = self._parser()
        args = p.parse_args(["diff", "a.log", "b.log"])
        assert args.fields == ["message", "level"]

    def test_custom_fields(self):
        p = self._parser()
        args = p.parse_args(["diff", "a.log", "b.log", "--fields", "source", "level"])
        assert args.fields == ["source", "level"]

    def test_format_default_text(self):
        p = self._parser()
        args = p.parse_args(["diff", "a.log", "b.log"])
        assert args.fmt == "text"

    def test_format_json(self):
        p = self._parser()
        args = p.parse_args(["diff", "a.log", "b.log", "--format", "json"])
        assert args.fmt == "json"

    def test_show_default_all(self):
        p = self._parser()
        args = p.parse_args(["diff", "a.log", "b.log"])
        assert args.show == "all"


class TestRunDiff:
    def _write(self, tmp_path, name, lines):
        p = tmp_path / name
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(p)

    def test_text_output_shows_added(self, tmp_path, capsys):
        left = self._write(tmp_path, "left.log", ['{"message": "old", "level": "INFO"}'])
        right = self._write(tmp_path, "right.log", [
            '{"message": "old", "level": "INFO"}',
            '{"message": "new", "level": "INFO"}',
        ])
        args = _make_args(left=left, right=right)
        run_diff(args)
        out = capsys.readouterr().out
        assert "+ new" in out

    def test_json_output_is_valid(self, tmp_path, capsys):
        left = self._write(tmp_path, "left.log", ['{"message": "a", "level": "INFO"}'])
        right = self._write(tmp_path, "right.log", ['{"message": "b", "level": "INFO"}'])
        args = _make_args(left=left, right=right, fmt="json")
        run_diff(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "added" in data
        assert "removed" in data

    def test_show_added_only(self, tmp_path, capsys):
        left = self._write(tmp_path, "left.log", ['{"message": "keep", "level": "INFO"}'])
        right = self._write(tmp_path, "right.log", [
            '{"message": "keep", "level": "INFO"}',
            '{"message": "extra", "level": "WARN"}',
        ])
        args = _make_args(left=left, right=right, fmt="json", show="added")
        run_diff(args)
        data = json.loads(capsys.readouterr().out)
        assert "removed" not in data
        assert len(data["added"]) == 1
