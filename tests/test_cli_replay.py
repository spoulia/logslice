"""Tests for logslice.cli_replay."""

import argparse
import datetime
import json
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from logslice.cli_replay import add_replay_subparser, run_replay, _read_entries


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": "-",
        "speed": 1.0,
        "max_delay": 5.0,
        "fmt": "plain",
        "func": run_replay,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddReplaySubparser:
    def _parser(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers()
        add_replay_subparser(sub)
        return p

    def test_subparser_registered(self):
        p = self._parser()
        ns = p.parse_args(["replay", "myfile.log"])
        assert ns.func is run_replay

    def test_speed_default(self):
        p = self._parser()
        ns = p.parse_args(["replay", "f.log"])
        assert ns.speed == 1.0

    def test_speed_custom(self):
        p = self._parser()
        ns = p.parse_args(["replay", "f.log", "--speed", "3.0"])
        assert ns.speed == pytest.approx(3.0)

    def test_max_delay_custom(self):
        p = self._parser()
        ns = p.parse_args(["replay", "f.log", "--max-delay", "10"])
        assert ns.max_delay == pytest.approx(10.0)

    def test_format_choices(self):
        p = self._parser()
        for fmt in ("plain", "json", "csv"):
            ns = p.parse_args(["replay", "f.log", "--format", fmt])
            assert ns.fmt == fmt


class TestReadEntries:
    def test_reads_from_stdin(self, monkeypatch):
        monkeypatch.setattr(sys, "stdin", StringIO("hello world\n"))
        entries = _read_entries("-")
        assert isinstance(entries, list)
        assert len(entries) == 1

    def test_reads_from_file(self, tmp_path):
        f = tmp_path / "test.log"
        f.write_text("2024-01-01T10:00:00 INFO starting\n")
        entries = _read_entries(str(f))
        assert len(entries) == 1

    def test_skips_blank_lines(self, tmp_path):
        f = tmp_path / "blank.log"
        f.write_text("line one\n\n   \nline two\n")
        entries = _read_entries(str(f))
        assert len(entries) == 2


class TestRunReplay:
    def test_prints_entries(self, tmp_path, capsys):
        f = tmp_path / "r.log"
        f.write_text("INFO hello\nINFO world\n")
        args = _make_args(file=str(f), speed=1.0, max_delay=0.0)
        with patch("logslice.replay.time.sleep"):
            run_replay(args)
        out = capsys.readouterr().out
        assert "hello" in out
        assert "world" in out
