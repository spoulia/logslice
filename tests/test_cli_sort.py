"""Tests for logslice.cli_sort."""

from __future__ import annotations

import argparse
import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from logslice.cli_sort import add_sort_subparser, run_sort


def _make_args(**kwargs):
    defaults = {
        "input": "-",
        "field": "timestamp",
        "extra_fields": [],
        "reverse": False,
        "missing_last": True,
        "func": run_sort,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_sort_subparser(sub)
    return p


class TestAddSortSubparser:
    def test_subparser_registered(self):
        p = _parser()
        args = p.parse_args(["sort"])
        assert hasattr(args, "func")

    def test_field_default(self):
        p = _parser()
        args = p.parse_args(["sort"])
        assert args.field == "timestamp"

    def test_reverse_default_false(self):
        p = _parser()
        args = p.parse_args(["sort"])
        assert args.reverse is False

    def test_reverse_flag(self):
        p = _parser()
        args = p.parse_args(["sort", "--reverse"])
        assert args.reverse is True

    def test_custom_field(self):
        p = _parser()
        args = p.parse_args(["sort", "--field", "level"])
        assert args.field == "level"

    def test_extra_fields(self):
        p = _parser()
        args = p.parse_args(["sort", "--extra-fields", "level", "message"])
        assert args.extra_fields == ["level", "message"]


class TestRunSort:
    def _run(self, entries, **kwargs):
        ndjson = "\n".join(json.dumps(e) for e in entries)
        args = _make_args(**kwargs)
        captured = StringIO()
        with patch("logslice.cli_sort._read_entries", return_value=entries):
            with patch("sys.stdout", captured):
                run_sort(args)
        return [json.loads(line) for line in captured.getvalue().splitlines() if line.strip()]

    def test_sorts_ascending(self):
        entries = [
            {"timestamp": "2024-01-03"},
            {"timestamp": "2024-01-01"},
            {"timestamp": "2024-01-02"},
        ]
        result = self._run(entries)
        assert [e["timestamp"] for e in result] == [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
        ]

    def test_sorts_descending(self):
        entries = [
            {"timestamp": "2024-01-01"},
            {"timestamp": "2024-01-03"},
        ]
        result = self._run(entries, reverse=True)
        assert result[0]["timestamp"] == "2024-01-03"

    def test_multi_field_sort_uses_stable_sort(self):
        entries = [
            {"timestamp": "2024-01-01", "level": "WARNING"},
            {"timestamp": "2024-01-01", "level": "ERROR"},
        ]
        result = self._run(entries, extra_fields=["level"])
        assert result[0]["level"] == "ERROR"

    def test_empty_input_produces_no_output(self):
        result = self._run([])
        assert result == []
