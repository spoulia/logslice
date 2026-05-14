"""Tests for logslice.cli_partition."""

from __future__ import annotations

import argparse
import json
from unittest.mock import patch

import pytest

from logslice.cli_partition import add_partition_subparser, run_partition


def _make_args(**kw) -> argparse.Namespace:
    defaults = {
        "field": "level",
        "patterns": [],
        "sizes_only": False,
        "input": "-",
    }
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_partition_subparser(sub)
    return p


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

class TestAddPartitionSubparser:
    def test_subparser_registered(self):
        p = _parser()
        ns = p.parse_args(["partition"])
        assert hasattr(ns, "func")

    def test_field_default(self):
        p = _parser()
        ns = p.parse_args(["partition"])
        assert ns.field == "level"

    def test_sizes_only_flag(self):
        p = _parser()
        ns = p.parse_args(["partition", "--sizes-only"])
        assert ns.sizes_only is True

    def test_pattern_argument_appends(self):
        p = _parser()
        ns = p.parse_args(["partition", "--pattern", "net=timeout", "--pattern", "disk=disk"])
        assert ns.patterns == ["net=timeout", "disk=disk"]


# ---------------------------------------------------------------------------
# run_partition
# ---------------------------------------------------------------------------

class TestRunPartition:
    def _entries(self):
        return [
            {"level": "info", "message": "started"},
            {"level": "error", "message": "failed"},
            {"level": "info", "message": "done"},
        ]

    def test_partition_by_field_output(self, capsys):
        args = _make_args()
        with patch("logslice.cli_partition._read_entries", return_value=self._entries()):
            run_partition(args)
        out = json.loads(capsys.readouterr().out)
        assert len(out["info"]) == 2
        assert len(out["error"]) == 1

    def test_sizes_only_returns_counts(self, capsys):
        args = _make_args(sizes_only=True)
        with patch("logslice.cli_partition._read_entries", return_value=self._entries()):
            run_partition(args)
        out = json.loads(capsys.readouterr().out)
        assert out["info"] == 2
        assert out["error"] == 1

    def test_invalid_pattern_exits(self):
        args = _make_args(patterns=["bad_pattern_no_equals"])
        with patch("logslice.cli_partition._read_entries", return_value=self._entries()):
            with pytest.raises(SystemExit):
                run_partition(args)

    def test_pattern_partition(self, capsys):
        args = _make_args(patterns=["failures=failed"], field="message")
        with patch("logslice.cli_partition._read_entries", return_value=self._entries()):
            run_partition(args)
        out = json.loads(capsys.readouterr().out)
        assert len(out["failures"]) == 1
